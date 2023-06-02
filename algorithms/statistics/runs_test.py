import numpy as np
from statsmodels.sandbox.stats.runs import runstest_1samp
from typing import Iterable


def classify_prices(prices: Iterable) -> np.array:
    print(np.where(np.diff(prices) > 0, 1, 0))
    return np.where(np.diff(prices) > 0, 1, 0)


def runs_test(prices: Iterable, p_value_threshold: float = None) -> bool or float:
    z_score, p_value = runstest_1samp(classify_prices(prices), cutoff=1, correction=False)

    return p_value < p_value_threshold if p_value_threshold else z_score, p_value