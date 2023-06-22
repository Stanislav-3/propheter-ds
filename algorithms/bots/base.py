import logging
from abc import ABC, abstractmethod
from datetime import datetime

from config.settings import SessionLocal
from models.models_ import Bot, Transaction
from algorithms.bots.base_enums import BotAction, BotStatus, BotMoneyMode, ReturnType
from exceptions.bot_exceptions import BotIsNotRunningError, BotModeIsNotConfiguredError
from api.data_api.views import buy_pair, sell_pair


class BotBase(ABC):
    def __init__(self):
        self.id = None
        self.key_id = None
        self.status = BotStatus.LOADING
        self.money_mode = BotMoneyMode.NOT_CONFIGURED
        self.pair = None
        self.invested_in_pair = False

        self.quote_asset_balance = 0
        self.base_asset_balance = 0
        self.total_balance_in_quote_asset = 0

        self.commission = 0.001

    def __repr__(self):
        return f'Name = {self.__class__.__name__}, id={self.id}'

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def step(self, new_price: float) -> None:
        pass

    def recalculate_total_balance(self, price: float = None):
        if price:
            self.total_balance_in_quote_asset = self.quote_asset_balance + self.base_asset_balance / price
        else:
            self.total_balance_in_quote_asset = self.quote_asset_balance

    def stop(self) -> None:
        # Set status in bot
        self.status = BotStatus.STOPPED

        # Set status in db
        db = SessionLocal()
        bot = db.query(Bot).get(self.id)
        bot.status = BotStatus.STOPPED
        db.commit()

    def buy(self, quote_amount: float, price: float):
        logging.info(f'Buy on {self.pair} with price={price} by bot={self}')
        db = SessionLocal()

        if self.money_mode == BotMoneyMode.REAL:
            order = await buy_pair(self.pair, self.key_id, quote_asset_quantity=quote_amount, db=db)
            price = order['price']
            base_asset_bought = order['base_asset_bought']
            quote_asset_sold = order['quote_asset_sold']
        else:
            # Paper money
            base_asset_bought = quote_amount / price * (1 - self.commission)
            quote_asset_sold = quote_amount

        # Update balances
        self.base_asset_balance += base_asset_bought
        self.quote_asset_balance -= quote_asset_sold
        self.recalculate_total_balance(price)

        # Add transaction to db
        transaction = Transaction(
            bot_id=self.id,
            date=datetime.now(),
            price=price,
            base_asset_amount=base_asset_bought,
            quote_asset_amount=quote_asset_sold,
            base_asset_balance=self.base_asset_balance,
            quote_asset_balance=self.quote_asset_balance,
            total_balance_in_quote_asset=self.total_balance_in_quote_asset,
            type=BotAction.BUY,
            money_mode=self.money_mode
        )
        db.add(transaction)
        db.commit()

    def sell(self, quote_amount: float, price: float):
        logging.info(f'Sell on {self.pair} with price={price} by bot={self}')
        db = SessionLocal()

        if self.money_mode == BotMoneyMode.REAL:
            order = await sell_pair(self.pair, self.key_id, quote_asset_quantity=quote_amount, db=db)
            price = order['price']
            base_asset_sold = order['base_asset_sold']
            quote_asset_bought = order['quote_asset_bought']
        else:
            # Paper money
            base_asset_sold = quote_amount / price
            quote_asset_bought = quote_amount * (1 - self.commission)

        # Update balances
        self.base_asset_balance -= base_asset_sold
        self.quote_asset_balance += quote_asset_bought
        self.recalculate_total_balance(price)

        # Add transaction to db
        transaction = Transaction(
            bot_id=self.id,
            date=datetime.now(),
            price=price,
            base_asset_amount=base_asset_sold,
            quote_asset_amount=quote_asset_bought,
            base_asset_balance=self.base_asset_balance,
            quote_asset_balance=self.quote_asset_balance,
            total_balance_in_quote_asset=self.total_balance_in_quote_asset,
            type=BotAction.SELL,
            money_mode=self.money_mode
        )
        db.add(transaction)
        db.commit()

    def verbose_total_balance(self, price: float):
        money = self.base_asset_balance / price + self.quote_asset_balance

        logging.info(f'Current balance for bot={self}:', money)

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
