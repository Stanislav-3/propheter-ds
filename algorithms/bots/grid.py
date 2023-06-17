import numpy as np
from algorithms.bots.base import BotBase, BotMoneyMode, ReturnType, BotStatus


class GridBot(BotBase):
    def __init__(self,
                 key_id: int,
                 pair: str,
                 min_level: float,
                 max_level: float,
                 max_money_to_invest: float,
                 money_mode: BotMoneyMode,
                 return_type: ReturnType,
                 levels_amount: int):
        super().__init__()
        self.key_id = key_id
        self.pair = pair
        self.min_level = min_level
        self.max_level = max_level

        self.max_money_to_invest = max_money_to_invest
        self.reserved_money = max_money_to_invest

        self.money_mode = money_mode
        self.return_type = return_type

        self.levels = None
        self.levels_amount = levels_amount
        self.money_to_trade = None
        self.invested_amount = 0.

    @staticmethod
    def check_parameters(levels_amount: int, money_to_trade: float, max_money_to_invest):
        if levels_amount <= 0:
            return ValueError(f'Levels_amount value should be greater than zero, '
                              f'but provided levels_amount={levels_amount}')
        if levels_amount % 2 != 0:
            return ValueError(f'Levels_amount value should be even, '
                              f'but provided levels_amount={levels_amount} is odd')

        if money_to_trade * levels_amount / 2 > max_money_to_invest:
            return ValueError(f'Money to trade per level multiplied by levels_amount / 2 '
                              f'should be less than all reserved money for trading')

    @staticmethod
    def adjust_grid(price: float, levels_amount: int) -> np.array:
        lower_boundary = price * 0.9
        upper_boundary = price * 1.1

        levels = np.linspace(lower_boundary, upper_boundary, num=levels_amount)
        return levels

    @staticmethod
    def check_grid(price: float, levels: np.array, money_to_trade) -> float:
        buy_amount = 0
        below_levels, above_levels = np.split(levels, 2)

        # can be optimized
        for level in below_levels:
            if price < level:
                buy_amount += money_to_trade

        # can be optimized
        for level in above_levels:
            if price > level:
                buy_amount -= money_to_trade

        return buy_amount

    def start(self) -> None:
        self.check_parameters(self.levels_amount, self.money_to_trade, self.max_money_to_invest)
        # todo: add real price
        price = np.random.random()
        self.levels = self.adjust_grid(price, self.levels_amount)
        self.status = BotStatus.RUNNING

    def step(self, new_price: float) -> None:
        self.check_is_running()
        self.check_money_mode_is_configured()

        investment_delta = self.check_grid(new_price, self.levels, self.money_to_trade)

        if investment_delta != 0:
            self.levels = self.adjust_grid(new_price, self.levels_amount)

            # sell
            if abs(investment_delta) > self.invested_amount:
                investment_delta = min(self.invested_amount, self.max_money_to_invest)

            if investment_delta > 0:
                self.buy()
            else:
                self.sell()
