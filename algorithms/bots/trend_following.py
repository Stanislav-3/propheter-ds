import numpy as np
import pandas as pd
import pandera as pa
from typing import Sequence, NamedTuple

from algorithms.bots.base import BotBase, BotEvaluationResult, BotAction, ReturnType, BotMoneyMode, BotStatus
from algorithms.preprocessing.returns import (
    get_log_returns, get_returns, from_log_returns_to_factor, from_returns_to_factor
)


class ScoreDataFrameSchema(pa.DataFrameModel):
    Price: pa.typing.Series[float]
    LogReturn: pa.typing.Series[float or np.nan]


class MovingWindows(NamedTuple):
    slow_window: int
    fast_window: int


# TODO: add option to use exp smoothing instead of SMA's
class TrendFollowingBot(BotBase):
    def __init__(self,
                 stock: str,
                 max_level: float,
                 min_level: float,
                 max_money_to_invest: float,
                 key_id: int,
                 money_mode: BotMoneyMode = None,
                 return_type: ReturnType = None,
                 slow_sma: int = None,
                 fast_sma: int = None):
        super().__init__()
        self.key_id = key_id
        self.pair = stock
        self.max_level = max_level
        self.min_level = min_level
        self.max_money_to_invest = max_money_to_invest
        self.money_mode = money_mode
        self.return_type = return_type
        self.slow_window = slow_sma
        self.fast_window = fast_sma

        self.invested_in_pair = False

        # todo make an request
        self.prices = []

        self.last_slow_average = None
        self.last_fast_average = None
        self.oldest_slow_value = None
        self.oldest_fast_value = None

        self.start()

    @staticmethod
    def check_sma_values(slow_window: int, fast_window: int, data_len: int) -> None:
        if fast_window <= 0 or slow_window <= 0:
            raise ValueError(f'Values should be greater than zero, but provided fast={fast_window}, slow={slow_window}')
        if fast_window >= slow_window:
            raise ValueError(f'Fast MA should be greater than slow, but provided fast={fast_window}, slow={slow_window}')
        if slow_window > data_len:
            raise ValueError(f'Not enough data for that high value of slow MA')

    def start(self) -> None:
        if self.slow_window and self.fast_window:
            self.check_sma_values(self.slow_window, self.fast_window, len(self.prices))
        else:
            best_moving_windows = self.search_parameters(self.prices, fast_min=1, fast_max=100,
                                                         slow_max=150, fast_slow_min_delta=1)
            self.slow_window = best_moving_windows.slow_window
            self.fast_window = best_moving_windows.fast_window

        # TODO: get prices from db or via request
        prices = self.prices

        self.last_slow_average = np.mean(prices[-self.slow_window:])
        self.last_fast_average = np.mean(prices[-self.fast_window:])

        self.oldest_slow_value = prices[-self.slow_window]
        self.oldest_fast_value = prices[-self.fast_window]

    def step(self, new_price) -> None:
        self.check_is_running()
        self.check_money_mode_is_configured()

        self.last_slow_average = (self.last_slow_average * self.slow_window
                                  - self.oldest_slow_value + new_price) / self.slow_window
        self.last_fast_average = (self.last_fast_average * self.fast_window
                                  - self.oldest_fast_value + new_price) / self.fast_window

        if not self.invested_in_pair and self.last_fast_average > self.last_slow_average:
            self.buy()
        elif self.invested_in_pair and self.last_fast_average < self.last_slow_average:
            self.sell()

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

    # todo: do it in separate process
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
