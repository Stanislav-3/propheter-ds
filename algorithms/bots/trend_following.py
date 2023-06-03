import numpy as np
import pandas as pd
import pandera as pa
from typing import Sequence, NamedTuple

from base import BotBase, BotEvaluationResult, ReturnType
from algorithms.preprocessing.returns import (
    get_log_returns, get_returns, from_log_returns_to_factor, from_returns_to_factor
)


class ScoreDataFrameSchema(pa.DataFrameModel):
    Price: pa.typing.Series[float]
    LogReturn: pa.typing.Series[float | np.nan]


class SMAParameters(NamedTuple):
    fast: int
    slow: int


# TODO: add option to use exp smoothing instead of SMA's
class TrendFollowingBot(BotBase):
    def __init__(self, slow_SMA=None, fast_SMA=None):
        super().__init__()

        if slow_SMA and fast_SMA:
            self.slow = slow_SMA
            self.fast = fast_SMA
        else:
            self.fast, self.slow = self.search_parameters(None, fast_min=1, fast_max=100, slow_max=150, fast_slow_min_delta=1)

    def start(self) -> None:
        super().start()

    def stop(self) -> None:
        super().stop()

    def evaluate(self) -> BotEvaluationResult:
        return super().evaluate()

    def score(self, df: pa.typing.DataFrame[ScoreDataFrameSchema], fast: int, slow: int) -> float:
        if fast <= 0 or slow <= 0:
            raise ValueError(f'Values should be greater than zero, but provided fast={fast}, slow={slow}')
        if fast >= slow:
            raise ValueError(f'Fast MA should be greater than slow, but provided fast={fast}, slow={slow}')
        if slow > len(df):
            raise ValueError(f'Not enough data for that high value of slow MA')

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
