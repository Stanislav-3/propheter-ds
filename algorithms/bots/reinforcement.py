import itertools
import logging
import numpy as np
import pandas as pd
import requests

from config.settings import DATA_API_URI
from algorithms.bots.base import BotBase, BotStatus, BotMoneyMode, ReturnType
from algorithms.preprocessing.returns import get_log_returns


feats = ['LogReturn']


class Env:
    def __init__(self, df):
        self.df = df
        self.n = len(df)
        self.current_idx = 0
        self.action_space = [0, 1, 2]  # BUY, SELL, HOLD
        self.invested = 0

        self.states = self.df[feats].to_numpy()
        self.rewards = self.df['LogReturnShifted'].to_numpy()

    def reset(self):
        self.current_idx = 0
        return self.states[self.current_idx]

    def step(self, action):
        # need to return (next_state, reward, done)

        self.current_idx += 1
        if self.current_idx >= self.n:
            raise Exception("Episode already done")

        if action == 0:  # BUY
            self.invested = 1
        elif action == 1:  # SELL
            self.invested = 0

        # compute reward
        if self.invested:
            reward = self.rewards[self.current_idx]
        else:
            reward = 0

        # state transition
        next_state = self.states[self.current_idx]

        done = (self.current_idx == self.n - 1)
        return next_state, reward, done


class StateMapper:
    def __init__(self, env, n_bins=6, n_samples=10000):
        # first, collect sample states from the environment
        states = []
        done = False
        s = env.reset()
        self.D = len(s)  # number of elements we need to bin
        states.append(s)

        while True:
            a = np.random.choice(env.action_space)
            s2, _, done = env.step(a)
            states.append(s2)
            if len(states) >= n_samples:
                break
            if done:
                s = env.reset()
                states.append(s)
                if len(states) >= n_samples:
                    break

        # convert to numpy array for easy indexing
        states = np.array(states)

        # create the bins for each dimension
        self.bins = []
        for d in range(self.D):
            column = np.sort(states[:, d])

            # find the boundaries for each bin
            current_bin = []
            for k in range(n_bins):
                boundary = column[int(n_samples / n_bins * (k + 0.5))]
                current_bin.append(boundary)

            self.bins.append(current_bin)

    def transform(self, state):
        x = np.zeros(self.D)

        for d in range(self.D):
            x[d] = int(np.digitize(state[d], self.bins[d]))
        return tuple(x)

    def all_possible_states(self):
        list_of_bins = []
        for d in range(self.D):
            list_of_bins.append(list(range(len(self.bins[d]) + 1)))
        # print(list_of_bins)
        return itertools.product(*list_of_bins)


class Agent:
    def __init__(self, action_size, state_mapper):
        self.action_size = action_size
        self.gamma = 0.8  # discount rate
        self.epsilon = 0.1
        self.learning_rate = 1e-1
        self.state_mapper = state_mapper

        # initialize Q-table randomly
        self.Q = {}
        for s in self.state_mapper.all_possible_states():
            s = tuple(s)
            for a in range(self.action_size):
                self.Q[(s, a)] = np.random.randn()

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return np.random.choice(self.action_size)

        s = self.state_mapper.transform(state)
        act_values = [self.Q[(s, a)] for a in range(self.action_size)]
        return np.argmax(act_values)  # returns action

    def train(self, state, action, reward, next_state, done):
        s = self.state_mapper.transform(state)
        s2 = self.state_mapper.transform(next_state)

        if done:
            target = reward
        else:
            act_values = [self.Q[(s2, a)] for a in range(self.action_size)]
            target = reward + self.gamma * np.amax(act_values)

        # Run one training step
        self.Q[(s, action)] += self.learning_rate * (target - self.Q[(s, action)])


def play_one_episode(agent, env, is_train):
    state = env.reset()
    done = False
    total_reward = 0

    while not done:
        action = agent.act(state)
        next_state, reward, done = env.step(action)
        total_reward += reward
        if is_train:
            agent.train(state, action, reward, next_state, done)
        state = next_state

    return total_reward


def get_is_invested(states):
    is_invested = False
    is_invested_list = []
    # [0, 1, 2] # BUY, SELL, HOLD

    for state in states:
        if state == 1:
            is_invested_list.append(False)

        if state == 0:
            is_invested_list.append(True)

        if state == 2:
            is_invested_list.append(is_invested)

        if state not in [0, 1, 2]:
            raise ValueError('Strange value')

    return is_invested_list


class ReinforcementBot(BotBase):
    def __init__(self,
                 id: int,
                 key_id: int,
                 pair: str,
                 min_level: float,
                 max_level: float,
                 max_money_to_invest: float,
                 money_mode: BotMoneyMode,
                 return_type: ReturnType):
        super().__init__()

        self.id = id
        self.key_id = key_id
        self.pair = pair
        self.min_level = min_level
        self.max_level = max_level
        self.max_money_to_invest = max_money_to_invest
        self.money_mode = money_mode
        self.return_type = return_type

        self.train_data = None
        self.test_data = None
        self.train_env = None
        self.test_env = None
        self.state_mapper = None
        self.agent = None

        self.test_ratio = 0.1
        self.num_episodes = 500
        self.last_price = None

        self.hold = False

        # todo: maybe start in other thread
        self.start()

    def start(self) -> None:
        self.set_loading()

        response = requests.get(f'{DATA_API_URI}/get-tick-prices/{self.pair}')
        log_returns = get_log_returns(response.json()['prices'])

        # Prepare data
        data = pd.DataFrame({
            'LogReturn': log_returns,
            'LogReturnShifted': log_returns.shift(1)
        })

        # Split into train and test
        n_test = int(len(data) * self.test_ratio)
        self.train_data = data.iloc[:-n_test]
        self.test_data = data.iloc[-n_test:]

        # Prepare environments
        self.train_env = Env(self.train_data)
        self.test_env = Env(self.test_data)

        # Prepare agent & StateMapper
        action_size = len(self.train_env.action_space)
        self.state_mapper = StateMapper(self.train_env)
        self.agent = Agent(action_size, self.state_mapper)

        # Prepare rewards
        train_rewards = np.empty(self.num_episodes)
        test_rewards = np.empty(self.num_episodes)

        for episode in range(self.num_episodes):
            train_reward = play_one_episode(self.agent, self.train_env, is_train=True)
            train_rewards[episode] = train_reward

            # test on the test set
            tmp_epsilon = self.agent.epsilon
            self.agent.epsilon = 0.
            test_reward = play_one_episode(self.agent, self.test_env, is_train=False)
            self.agent.epsilon = tmp_epsilon
            test_rewards[episode] = test_reward

            logging.info(f"Bot:{self}, eps: {episode + 1}/{self.num_episodes}, train: {train_reward:.5f}, test: {test_reward:.5f}")

        self.set_running()

    def step(self, new_price) -> None:
        if self.status != BotStatus.RUNNING:
            self.last_price = new_price
            return

        state = np.log(new_price - self.last_price)
        action = self.agent.act(state)

        if not self.hold and action == 0:
            self.hold = True
            self.buy(self.bot_balance, new_price)
        elif self.hold and action == 1:
            self.hold = False
            self.sell(1, new_price)
