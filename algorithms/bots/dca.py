import time

from algorithms.bots.base import BotBase, BotMoneyMode, ReturnType, BotStatus


class DCABot(BotBase):
    def __init__(self,
                 key_id: int,
                 pair: str,
                 max_money_to_invest: float,
                 money_mode: BotMoneyMode,
                 return_type: ReturnType,
                 money_to_invest: float,
                 investment_interval: int):
        super().__init__()
        self.key_id = key_id
        self.pair = pair
        self.money_mode = money_mode
        self.return_type = return_type
        self.money_to_invest = money_to_invest
        self.investment_interval = investment_interval
        self.next_investment_time = None

        self.start()

    def start(self) -> None:
        self.status = BotStatus.RUNNING

    def step(self, new_price) -> None:
        self.check_is_running()
        self.check_money_mode_is_configured()

        if self.next_investment_time <= time.time():
            return

        self.buy()
        self.next_investment_time += self.investment_interval
