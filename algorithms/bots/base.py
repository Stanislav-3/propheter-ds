import logging
from abc import ABC, abstractmethod
from datetime import datetime

from config.settings import SessionLocal
from models.models_ import Bot, Transaction
from algorithms.bots.base_enums import BotAction, BotStatus, BotMoneyMode, ReturnType
from exceptions.bot_exceptions import BotIsNotRunningError, BotModeIsNotConfiguredError


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

    @abstractmethod
    def step(self, new_price: float) -> None:
        pass

    def stop(self) -> None:
        # Set status in bot
        self.status = BotStatus.STOPPED

        # Set status in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.STOPPED
        db.commit()

    def buy(self, amount: float, price: float):
        logging.info(f'Buy on {self.pair} with price={price} by bot={self}')

        if self.money_mode == BotMoneyMode.PAPER:
            self.paper_money *= price

        elif self.money_mode == BotMoneyMode.REAL:
            # todo: add transaction to db an request to data api
            pass

        # Add transaction to db
        transaction = Transaction(
            bot_id=self.id,
            date=datetime.now(),
            # todo: add real price if real trade
            price=price,
            # todo: add real amount if real trade
            amount=amount,
            type=BotAction.BUY,
            money_mode=self.money_mode
        )
        db = SessionLocal()
        db.add(transaction)
        db.commit()

    def sell(self, amount: float, price: float):
        logging.info(f'Sell on {self.pair} with price={price} by bot={self}')

        if self.money_mode == BotMoneyMode.PAPER:
            self.paper_money /= price
        elif self.money_mode == BotMoneyMode.REAL:
            # todo: add transaction to db an request to data api
            pass

        # Add transaction to db
        transaction = Transaction(
            bot_id=self.id,
            date=datetime.now(),
            # todo: add real price if real trade
            price=price,
            # todo: add real amount if real trade
            amount=amount,
            type=BotAction.SELL,
            money_mode=self.money_mode
        )
        db = SessionLocal()
        db.add(transaction)
        db.commit()

    def verbose_price(self, price: float):
        if self.money_mode == BotMoneyMode.PAPER:
            if self.invested_in_pair:
                money = self.paper_money / price
            else:
                money = self.paper_money

            logging.info(f'Current paper balance for bot={self}:', money)

    def set_loading(self):
        logging.info(f'Set loading for bot {self}')

        # Set status in bot
        self.status = BotStatus.LOADING

        # Set status in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.LOADING
        db.commit()

    def set_running(self):
        logging.info(f'Set running for bot {self}')

        # Set status in bot
        self.status = BotStatus.RUNNING

        # Set status in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.RUNNING
        db.commit()
