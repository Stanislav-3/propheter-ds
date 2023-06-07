import numpy as np
import pandas as pd
import pandera as pa
from typing import Sequence, NamedTuple

from base import BotBase, BotEvaluationResult, BotAction, ReturnType
from algorithms.preprocessing.returns import (
    get_log_returns, get_returns, from_log_returns_to_factor, from_returns_to_factor
)


class ScoreDataFrameSchema(pa.DataFrameModel):
    Price: pa.typing.Series[float]
    LogReturn: pa.typing.Series[float | np.nan]


class SMAParameters(NamedTuple):
    slow: int
    fast: int


# TODO: add option to use exp smoothing instead of SMA's
class TrendFollowingBot(BotBase):
    def __init__(self, prices: Sequence, slow_sma: int = None, fast_sma: int = None):
        super().__init__()

        self.last_slow_average = None
        self.last_fast_average = None

        self.oldest_slow_value = None
        self.oldest_fast_value = None

        if slow_sma and fast_sma:
            self.check_sma_values(slow_sma, fast_sma, len(prices))
            self.slow_window = slow_sma
            self.fast_window = fast_sma
        else:
            parameters = self.search_parameters(prices, fast_min=1, fast_max=100, slow_max=150, fast_slow_min_delta=1)
            self.slow_window, self.fast_window = parameters.slow, parameters.fast

        self.start()

    @staticmethod
    def check_sma_values(slow_sma: int, fast_sma: int, data_len: int) -> None:
        if fast_sma <= 0 or slow_sma <= 0:
            raise ValueError(f'Values should be greater than zero, but provided fast={fast_sma}, slow={slow_sma}')
        if fast_sma >= slow_sma:
            raise ValueError(f'Fast MA should be greater than slow, but provided fast={fast_sma}, slow={slow_sma}')
        if slow_sma > data_len:
            raise ValueError(f'Not enough data for that high value of slow MA')

    def start(self) -> None:
        super().start()

        # TODO: get prices from db or via request
        prices = []

        self.last_slow_average = np.mean(prices[-self.slow_window:])
        self.last_fast_average = np.mean(prices[-self.fast_window:])

        self.oldest_slow_value = prices[-self.slow_window]
        self.oldest_fast_value = prices[-self.fast_window]

    def stop(self) -> None:
        super().stop()

    def step(self, new_price) -> BotEvaluationResult:
        self.last_slow_average = (self.last_slow_average * self.slow_window
                                  - self.oldest_slow_value + new_price) / self.slow_window
        self.last_fast_average = (self.last_fast_average * self.fast_window
                                  - self.oldest_fast_value + new_price) / self.fast_window
        # todo: add transaction to db
        if not self.hold_asset and self.last_fast_average > self.last_slow_average:
            return BotEvaluationResult(action=BotAction.BUY)
        elif self.hold_asset and self.last_fast_average < self.last_slow_average:
            return BotEvaluationResult(action=BotAction.SELL)
        else:
            return BotEvaluationResult(action=BotAction.DO_NOTHING)

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

    def search_parameters(self, prices: Sequence,
                          fast_min: int, fast_max: int, slow_max: int, fast_slow_min_delta: int) -> SMAParameters:
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

        return SMAParameters(fast=best_fast, slow=best_slow)
