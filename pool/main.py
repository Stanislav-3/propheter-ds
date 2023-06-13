from pool.pool import Pool
from typing import Generator


pool = Pool()


def get_pool() -> Generator:
    yield pool
