import threading
from functools import wraps
import time
import asyncio
import numpy as np


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        print(f'Function {func.__name__}{args}{kwargs} Took {end_time - start_time:.4f} seconds')
        return result
    return wrapper


BOTS_NUMBER = 100
SLEEP_TIME = 0.5
COMPUTATIONS_RANGE = 1000


class TestBot:
    def step(self):
        x = 2
        for i in range(COMPUTATIONS_RANGE):
            x *= np.log2(x)
        time.sleep(SLEEP_TIME)
        for i in range(COMPUTATIONS_RANGE):
            x *= np.log2(x)
        time.sleep(SLEEP_TIME)
        return x


class TestBotAsync:
    async def step(self):
        x = 2
        for i in range(COMPUTATIONS_RANGE):
            x *= np.log2(x)
        await asyncio.sleep(SLEEP_TIME)
        for i in range(COMPUTATIONS_RANGE):
            x *= np.log2(x)
        await asyncio.sleep(SLEEP_TIME)
        return x


bots = [TestBot() for _ in range(BOTS_NUMBER)]
bots_async = [TestBotAsync() for _ in range(BOTS_NUMBER)]


@timeit
def simple():
    for bot in bots:
        bot.step()


@timeit
def threads():
    threads = []

    for bot in bots:
        threads.append(threading.Thread(target=bot.step))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


@timeit
def simple_async():
    async def run():
        await asyncio.gather(*[bot.step() for bot in bots_async])

    asyncio.run(run())


# simple()
threads()
simple_async()
