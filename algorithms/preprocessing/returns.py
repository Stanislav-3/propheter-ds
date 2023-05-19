import numpy as np
import pandas as pd
from typing import Iterable


def get_log_returns(prices: Iterable, remove_first: bool = True) -> np.array:
    start_idx = 1 if remove_first else 0
    return np.log(pd.Series(prices)).diff().values[start_idx:]


def get_returns(prices: Iterable, remove_first: bool = True) -> np.array:
    start_idx = 1 if remove_first else 0
    return pd.Series(prices).pct_change()[start_idx:]


