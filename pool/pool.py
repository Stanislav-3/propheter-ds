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
            logging.info('bot appended to pool')
        except KeyError:
            logging.info('try to add new bot pool')
            self.stock_bots_mapping[stock_name] = [bot]
            logging.info('new bot added to pool')

        logging.info(f"Successfully added new stock to pool. Pool={self.stock_bots_mapping}")

    def remove(self, stock_name: str, bot_id: int) -> bool:
        logging.info(f'pool.remove(pair={stock_name}, bot_id={bot_id})')

        # get bots on pair
        bots = self.stock_bots_mapping.get(stock_name)
        if bots is None:
            logging.info(f'There is no bots on pair {stock_name}')
            return False

        # remove bot
        removed = False
        for bot in bots:
            if bot.id == bot_id:
                logging.info(f'Remove bot {bot} from pool pair={stock_name}')
                self.stock_bots_mapping[stock_name].remove(bot)
                del bot
                removed = True

        if not removed:
            return False

        # delete pair from pool if no bots are on it
        if len(self.stock_bots_mapping[stock_name]) == 0:
            logging.info(f'Remove stock_name={stock_name} from pool')
            del self.stock_bots_mapping[stock_name]

        return True

    def run_bots(self, stock_name: str, new_price: float):
        logging.info(f'Pool.run_bots() | stock_bots_mapping={self.stock_bots_mapping}')
        bots = self.stock_bots_mapping[stock_name]

        # todo: add multithreading
        for bot in bots:
            bot.step(new_price)

    def get_bot(self, bot_id: int) -> None or TrendFollowingBot:
        bots_lists = self.stock_bots_mapping.values()

        for bots in bots_lists:
            for bot in bots:
                if bot.id == bot_id:
                    return bot

        return None
