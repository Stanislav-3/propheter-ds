import numpy as np
import pandas as pd
from typing import Iterable


def get_log_returns(prices: Iterable, remove_first: bool = True) -> np.array:
    start_idx = 1 if remove_first else 0
    return np.log(pd.Series(prices)).diff().values[start_idx:]


def get_returns(prices: Iterable, remove_first: bool = True) -> np.array:
    start_idx = 1 if remove_first else 0
    return pd.Series(prices).pct_change()[start_idx:]


def from_log_returns_to_factor(log_returns: Iterable, exponentialize: bool = True) -> np.float64:
    return np.exp(np.sum(log_returns)) if exponentialize else np.sum(log_returns)


def from_returns_to_factor(returns: Iterable) -> np.float64:
    return np.prod(1 + np.array(returns))
