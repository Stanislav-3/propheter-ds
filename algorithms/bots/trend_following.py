import logging
import numpy as np
import pandas as pd
import pandera as pa
from typing import Sequence, NamedTuple

from config.settings import SessionLocal
from models.models_ import Bot
from algorithms.bots.base import BotBase, ReturnType, BotMoneyMode, BotStatus
from algorithms.preprocessing.returns import (
    get_log_returns, get_returns, from_log_returns_to_factor, from_returns_to_factor
)


class ScoreDataFrameSchema(pa.DataFrameModel):
    Price: pa.typing.Series[float]
    LogReturn: pa.typing.Series[float or np.nan]


class MovingWindows(NamedTuple):
    slow_window: int
    fast_window: int


class TrendFollowingBot(BotBase):
    def __init__(self,
                 id: int,
                 key_id: int,
                 pair: str,
                 min_level: float,
                 max_level: float,
                 max_money_to_invest: float,
                 money_mode: BotMoneyMode = None,
                 return_type: ReturnType = None,
                 slow_window: int = None,
                 fast_window: int = None):
        super().__init__()
        self.id = id
        self.key_id = key_id
        self.pair = pair
        self.min_level = min_level
        self.max_level = max_level
        self.max_money_to_invest = max_money_to_invest
        self.money_to_invest = max_money_to_invest
        self.money_mode = money_mode
        self.return_type = return_type
        self.slow_window = slow_window
        self.fast_window = fast_window

        self.loading_prices = []

        self.slow_sma = None
        self.fast_sma = None
        self.oldest_slow_price = None
        self.oldest_fast_price = None

        self.start()

    @staticmethod
    def check_sma_values(slow_window: int, fast_window: int, upper_bound: int) -> None:
        if fast_window <= 0 or slow_window <= 0:
            raise ValueError(f'Values should be greater than zero, but provided fast={fast_window}, slow={slow_window}')
        if fast_window >= slow_window:
            raise ValueError(f'Fast MA should be greater than slow, but provided fast={fast_window}, slow={slow_window}')
        if slow_window > upper_bound:
            raise ValueError(f'Too high value of slow MA. It should be less than {upper_bound}')

    def start(self) -> None:
        self.status = BotStatus.LOADING

        if self.slow_window and self.fast_window:
            self.check_sma_values(self.slow_window, self.fast_window, 200)
        else:
            # todo: change prices
            best_moving_windows = self.search_parameters(self.loading_prices, fast_min=1, fast_max=100,
                                                         slow_max=150, fast_slow_min_delta=1)
            self.slow_window = best_moving_windows.slow_window
            self.fast_window = best_moving_windows.fast_window

    def step(self, new_price: int) -> None:
        logging.info(f'Step for bot={self}')

        if self.status == BotStatus.LOADING:
            self.loading_step(new_price)
        elif self.status == BotStatus.RUNNING:
            self.running_step(new_price)

    def loading_step(self, new_price: int):
        logging.info(f'Loading step for bot={self}')

        self.loading_prices.append(new_price)
        
        if len(self.loading_prices) != self.slow_window:
            return 

        self.slow_sma = np.mean(self.loading_prices)
        self.fast_sma = np.mean(self.loading_prices[-self.fast_window:])

        self.oldest_slow_price = self.loading_prices[-self.slow_window]
        self.oldest_fast_price = self.loading_prices[-self.fast_window]

        self.loading_prices.clear()
        self.status = BotStatus.RUNNING

        # Set status to running in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.RUNNING
        db.commit()

    def running_step(self, new_price):
        logging.info(f'Running step for bot={self}')

        self.slow_sma = (self.slow_sma * self.slow_window - self.oldest_slow_price + new_price) / self.slow_window
        self.fast_sma = (self.fast_sma * self.fast_window - self.oldest_fast_price + new_price) / self.fast_window

        if not self.invested_in_pair and self.fast_sma > self.slow_sma:
            self.buy(self.max_money_to_invest)
            self.invested_in_pair = True
        elif self.invested_in_pair and self.fast_sma < self.slow_sma:
            self.sell(self.max_money_to_invest)
            self.invested_in_pair = False

        self.verbose_price(new_price)

    def score(self, df: pa.typing.DataFrame[ScoreDataFrameSchema], fast: int, slow: int) -> float:
        self.check_sma_values(fast, slow, len(df))

        df['SlowSMA'] = df['Price'].rolling(slow).mean()
        df['FastSMA'] = df['Price'].rolling(fast).mean()

        df['Signal'] = np.where(df['FastSMA'] >= df['SlowSMA'], 1, 0)
        df['AlgoSomeReturn'] = df['Signal'].astype(bool) * df['SomeReturn']

        if self.return_type == ReturnType.LOG_RETURN:
            return from_log_returns_to_factor(df['AlgoSomeReturn'].values, exponentialize=False)
        elif self.return_type == ReturnType.RETURN:
            return from_returns_to_factor(df['AlgoSomeReturn'].values)
        else:
            raise Exception(f'Unknown return type: {self.return_type.name}')

    def search_parameters(self,
                          prices: Sequence,
                          fast_min: int,
                          fast_max: int,
                          slow_max: int,
                          fast_slow_min_delta: int) -> MovingWindows:
        best_fast, best_slow = None, None
        best_score = float('-inf')

        some_return = get_log_returns(prices) if self.return_type == ReturnType.LOG_RETURN else get_returns(prices)
        df = pd.DataFrame({
            'Price': prices,
            'AnyReturn': some_return
        })

        for fast in range(fast_min, fast_max):
            for slow in range(fast + fast_slow_min_delta, slow_max):
                score = self.score(df, fast, slow)
                if score > best_score:
                    best_fast = fast
                    best_slow = slow
                    best_score = score

        return MovingWindows(slow_window=best_slow, fast_window=best_fast)
