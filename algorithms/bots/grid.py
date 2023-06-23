import logging
import numpy as np
from enum import Enum
from algorithms.bots.base import BotBase, BotMoneyMode, ReturnType, BotStatus
from algorithms.bots.base_enums import RunningMode


class GridBot(BotBase):
    def __init__(self,
                 id: int,
                 key_id: int,
                 pair: str,
                 min_level: float,
                 max_level: float,
                 max_money_to_invest: float,
                 money_to_trade: float,
                 money_mode: BotMoneyMode,
                 return_type: ReturnType,
                 levels_amount: int,
                 running_mode: RunningMode,
                 boundary_factor: float = 0.1):
        super().__init__()
        self.id = id
        self.key_id = key_id
        self.pair = pair
        self.min_level = min_level
        self.max_level = max_level

        self.quote_asset_balance = max_money_to_invest
        self.max_money_to_invest = max_money_to_invest
        self.reserved_money = max_money_to_invest

        self.money_mode = money_mode
        self.return_type = return_type

        self.levels = None
        self.levels_amount = levels_amount
        self.money_to_trade = money_to_trade
        self.invested_amount = 0.

        self.boundary_factor = boundary_factor
        self.running_mode = running_mode

        self.start()

    def check_parameters(self):
        if self.levels_amount <= 0 or self.levels_amount > 50:
            raise ValueError(f'Levels_amount value should be greater than zero and not greater than 50, '
                             f'but provided levels_amount={self.levels_amount}')
        if self.levels_amount % 2 != 0:
            raise ValueError(f'Levels_amount value should be even, '
                             f'but provided levels_amount={self.levels_amount} is odd')

        if self.money_to_trade * self.levels_amount / 2 > self.max_money_to_invest:
            raise ValueError(f'Money to trade per level multiplied by levels_amount / 2 '
                             f'should be less than all reserved money for trading')

        if self.running_mode == RunningMode.DYNAMIC \
                and (self.boundary_factor < 0.1 or self.boundary_factor > 0.9):
            raise ValueError(f'Boundary factor should be less than 0.9 and greater than 0.1, '
                             f'but provided boundary_factor={self.boundary_factor}')

    def get_levels_for_adjusted_grid(self, price: float) -> np.array:
        lower_boundary = price * (1 - self.boundary_factor)
        upper_boundary = price * (1 + self.boundary_factor)

        levels = np.linspace(lower_boundary, upper_boundary, num=self.levels_amount)
        return levels

    def check_grid(self, price: float) -> float:
        buy_amount = 0
        below_levels, above_levels = np.split(self.levels, 2)

        # todo: can be optimized
        for level in below_levels:
            if price < level:
                buy_amount += self.money_to_trade

        # todo: can be optimized
        for level in above_levels:
            if price > level:
                buy_amount -= self.money_to_trade

        return buy_amount

    def start(self) -> None:
        self.check_parameters()
        self.set_loading()

    def step(self, new_price: float) -> None:
        logging.info(f'Step for bot={self}')

        if self.status == BotStatus.LOADING:
            self.loading_step(new_price)
        elif self.status == BotStatus.RUNNING:
            self.running_step(new_price)

    def loading_step(self, new_price):
        logging.info(f'Loading step for bot={self}')
        self.levels = self.get_levels_for_adjusted_grid(new_price)
        self.set_running()

    def running_step(self, new_price):
        logging.info(f'Running step for bot={self}')
        investment_delta = self.check_grid(new_price)

        if investment_delta != 0:
            # Adjust grid if bot is dynamic
            if self.running_mode == RunningMode.DYNAMIC:
                self.levels = self.get_levels_for_adjusted_grid(new_price)

            # Sell
            if investment_delta < 0:
                # Ensure bot doesn't sell to much
                # if abs(investment_delta) > self.invested_amount:
                #     investment_delta = -self.invested_amount

                sell_amount = min(abs(investment_delta), self.base_asset_balance * new_price)
                self.sell(sell_amount, new_price)
            # Buy
            else:
                # Ensure bot doesn't buy to much
                buy_mount = min(investment_delta, self.quote_asset_balance)

                self.buy(buy_mount, new_price)
