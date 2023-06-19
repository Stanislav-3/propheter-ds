import logging

from exceptions.pool_exceptions import PoolExistsError
from algorithms.bots.base import BotBase
from algorithms.bots.trend_following import TrendFollowingBot


# TODO: WHAT happens if server had gone down, and how to restore it
# also restore if bot is in db but is not in pool
class Pool:
    is_created = False

    def __new__(cls, *args, **kwargs):
        if cls.is_created:
            raise PoolExistsError('Pool is already instantiated. There can be only one instance of Pool class')

        cls.is_created = True
        return super().__new__(cls)

    def __init__(self):
        self.stock_bots_mapping = {}

    def add(self, stock_name: str, bot: BotBase):
        try:
            self.stock_bots_mapping[stock_name].append(bot)
        except KeyError:
            self.stock_bots_mapping[stock_name] = [bot]

        logging.info("Successfully added new stock to pool")

    def remove(self, stock_name, bot):
        #  TODO: think about that
        self.stock_bots_mapping[stock_name].remove(bot)

        if len(self.stock_bots_mapping[stock_name]) == 0:
            del self.stock_bots_mapping[stock_name]

    def run_bots(self, stock_name: str, new_price: float):
        logging.info(f'Pool.run_bots() | stock_bots_mapping={self.stock_bots_mapping}')
        bots = self.stock_bots_mapping[stock_name]

        # TODO: THINK ABOUT BOTS IN TERMS OF PARALLELISM
        for bot in bots:
            bot.step(new_price)

    def get_bot(self, bot_id: int) -> None or TrendFollowingBot:
        bots_lists = self.stock_bots_mapping.values()

        for bots in bots_lists:
            for bot in bots:
                if bot.id == bot_id:
                    return bot

        return None
