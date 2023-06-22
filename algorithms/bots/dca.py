import time
from enum import Enum

from algorithms.bots.base import BotBase, BotMoneyMode, ReturnType, BotStatus


class InvestmentIntervalScale(Enum):
    MINUTE = 'Minute'
    HOUR = 'Hour'
    DAY = 'Day'


class DCABot(BotBase):
    def __init__(self,
                 key_id: int,
                 pair: str,
                 max_money_to_invest: float,
                 money_mode: BotMoneyMode,
                 return_type: ReturnType,
                 investment_money: float,
                 investment_interval: int,
                 investment_interval_scale: InvestmentIntervalScale):
        super().__init__()
        self.key_id = key_id
        self.pair = pair
        self.money_mode = money_mode
        self.return_type = return_type

        self.investment_money = investment_money
        self.investment_interval = investment_interval
        self.investment_interval_scale = investment_interval_scale
        self.investment_interval_in_seconds = self.get_investment_interval_in_seconds()

        self.next_investment_time = 0.

        self.start()

    def start(self) -> None:
        self.next_investment_time = time.time()
        self.set_running()

    def step(self, new_price) -> None:
        if self.status != BotStatus.RUNNING:
            return

        # Check if it's time to invest
        if self.next_investment_time >= time.time():
            return

        # Update next investment date and invest in pair
        self.next_investment_time += self.investment_interval_in_seconds
        self.buy(new_price)

    def get_investment_interval_in_seconds(self) -> float:
        if self.investment_interval_scale == InvestmentIntervalScale.MINUTE:
            return self.investment_interval * 60
        elif self.investment_interval_scale == InvestmentIntervalScale.HOUR:
            return self.investment_interval * 60 * 60
        elif self.investment_interval_scale == InvestmentIntervalScale.DAY:
            return self.investment_interval * 60 * 60 * 24
