from abc import ABC, abstractmethod
from enum import Enum

import requests

from exceptions.bot_exceptions import BotIsNotRunningError, BotModeIsNotConfiguredError
from typing import NamedTuple


class BotStatus(Enum):
    LOADING = 'Loading'
    RUNNING = 'Running'
    STOPPED = 'Stopped'


class BotMoneyMode(Enum):
    REAL = 'Real'
    PAPER = 'Paper'
    NOT_CONFIGURED = 'Not configured'


class ReturnType(Enum):
    LOG_RETURN = 'Log_return'
    RETURN = 'Return'


class BotAction(Enum):
    BUY = 'Buy'
    HOLD = 'Hold'
    SELL = 'Sell'
    DO_NOTHING = 'Do nothing'


class BotBase(ABC):
    def __init__(self):
        self.id = None
        self.status = BotStatus.LOADING
        self.money_mode = BotMoneyMode.NOT_CONFIGURED
        self.paper_money = 1000
        self.pair = None
        self.invested_in_pair = False

    def __repr__(self):
        return f'Name = {self.__class__.__name__}, id={self.id}'

    @abstractmethod
    def start(self) -> None:
        pass

    def stop(self) -> None:
        self.status = BotStatus.STOPPED

    @abstractmethod
    def step(self, new_price: float) -> None:
        pass

    def check_is_running(self) -> None:
        if self.status != BotStatus.RUNNING:
            raise BotIsNotRunningError(f'You cannot use bot "{self.__class__.__name__}"'
                                       f'because it is still not configured')

    def check_money_mode_is_configured(self) -> None:
        if self.money_mode == BotMoneyMode.NOT_CONFIGURED:
            raise BotModeIsNotConfiguredError(f'Money mode of bot "{self.__class__.__name__}" is not configured')

    def buy(self, price: float):
        print('BUY')
        if self.money_mode == BotMoneyMode.PAPER:
            self.paper_money *= price

        elif self.money_mode == BotMoneyMode.REAL:
            # todo: add transaction to db an request to data api
            pass

    def sell(self, price: float):
        print('SELL')
        if self.money_mode == BotMoneyMode.PAPER:
            self.paper_money /= price
        elif self.money_mode == BotMoneyMode.REAL:
            # todo: add transaction to db an request to data api
            pass

    def verbose_price(self, price: float):
        if self.money_mode == BotMoneyMode.PAPER:
            if self.invested_in_pair:
                money = self.paper_money / price
            else:
                money = self.paper_money

            print('Current paper balance:', money)
