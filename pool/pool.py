from exceptions.pool_exceptions import PoolExistsError
from algorithms.bots.base import BotBase


# TODO: make a better name instead of stock (cause we got stock-to-stock relations)
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

    def remove(self, stock_name, bot):
        #  TODO: think about that
        self.stock_bots_mapping[stock_name].remove(bot)

        if len(self.stock_bots_mapping[stock_name]) == 0:
            del self.stock_bots_mapping[stock_name]

    def run_bots(self, stock_name: str):
        # TODO: THINK ABOUT BOTS IN TERMS OF PARALLELISM
        bots = self.stock_bots_mapping[stock_name]

    def get_bot(self, bot_id: int) -> BotBase or None:
        bots_lists = self.stock_bots_mapping.values()

        for bots in bots_lists:
            for bot in bots:
                if bot.id == bot_id:
                    return bot

        return None
