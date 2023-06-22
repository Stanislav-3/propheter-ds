import logging
from abc import ABC, abstractmethod
from enum import Enum
import requests

from config.settings import SessionLocal
from models.models_ import Bot
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

        self.bot_balance = 0
        self.money_invested = 0
        self.money_in_pair = 0

    def __repr__(self):
        return f'Name = {self.__class__.__name__}, id={self.id}'

    @abstractmethod
    def start(self) -> None:
        pass

    def stop(self) -> None:
        # Set status in bot
        self.status = BotStatus.STOPPED

        # Set status in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.STOPPED
        db.commit()

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
        logging.info(f'Buy on {self.pair} with price={price} by bot={self}')

        if self.money_mode == BotMoneyMode.PAPER:
            self.paper_money *= price

        elif self.money_mode == BotMoneyMode.REAL:
            # todo: add transaction to db an request to data api
            pass

    def sell(self, price: float):
        logging.info(f'Sell on {self.pair} with price={price} by bot={self}')

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

            logging.info(f'Current paper balance for bot={self}:', money)

    def set_loading(self):
        # Set status in bot
        self.status = BotStatus.LOADING

        # Set status in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.LOADING
        db.commit()

    def set_running(self):
        # Set status in bot
        self.status = BotStatus.RUNNING

        # Set status in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.RUNNING
        db.commit()

