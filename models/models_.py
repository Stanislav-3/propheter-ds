from sqlalchemy import ForeignKey, Column, String, Integer, CHAR, Text, LargeBinary, DateTime, DECIMAL, Enum, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type

from config.settings import Base
from algorithms.bots.base_enums import BotMoneyMode, ReturnType, BotStatus, BotAction


class BotType(Base):
    """
    Implemented bot types.

    """

    __tablename__ = 'BotTypes'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    name = Column(String(32))
    parameters_schema = Column(mutable_json_type(dbtype=JSONB, nested=True))

    def __repr__(self):
        return f'id={self.id}, name={self.name}, parameters_schema={self.parameters_schema}'


class Bot(Base):
    """
    Implemented bots.

    """

    __tablename__ = 'Bots'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    stock_id = Column(ForeignKey('Stocks.id', ondelete='CASCADE'))
    bot_type_id = Column(ForeignKey('BotTypes.id', ondelete='CASCADE'))
    key_id = Column(ForeignKey('Keys.id'), nullable=True)

    status = Column(Enum(BotStatus))
    parameters = Column(mutable_json_type(dbtype=JSONB, nested=True))
    max_money_to_invest = Column(DECIMAL(precision=32, scale=17))
    max_level = Column(DECIMAL(precision=32, scale=17))
    min_level = Column(DECIMAL(precision=32, scale=17))
    money_mode = Column(Enum(BotMoneyMode))
    return_type = Column(Enum(ReturnType))

    def __repr__(self):
        return f'id={self.id}, stock_id={self.stock_id}, bot_type_id={self.bot_type_id}, key_id={self.key_id}, ' \
               f'parameters={self.parameters}, max_money_to_invest={self.max_money_to_invest}, ' \
               f'max_level={self.max_level}, min_level={self.min_level}'

    def __str__(self):
        return f'id={self.id}, stock_id={self.stock_id}, bot_type_id={self.bot_type_id}, key_id={self.key_id}, ' \
               f'parameters={self.parameters}'


class Stock(Base):
    """
    Stocks data
    """

    __tablename__ = 'Stocks'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    name = Column(String(16), unique=True)

    def __repr__(self):
        return f'id={self.id}, name={self.name}'


class Kline(Base):
    """
    Stocks data
    """

    __tablename__ = 'Klines'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    stock_id = Column(ForeignKey('Stocks.id', ondelete='CASCADE'))

    date = Column(DateTime())
    low = Column(DECIMAL(precision=32, scale=17))
    high = Column(DECIMAL(precision=32, scale=17))
    open = Column(DECIMAL(precision=32, scale=17))
    close = Column(DECIMAL(precision=32, scale=17))
    volume = Column(DECIMAL(precision=32, scale=17))

    def __repr__(self):
        return f'id={self.id}, stock_id={self.stock_id}, date={self.date}, low={self.low}, high={self.high}, ' \
               f'open={self.open}, close={self.close}, volume={self.volume}'

    def __str__(self):
        return f'id={self.id}, stock_id={self.stock_id}'


class Key(Base):
    """
    Keys for exchange
    """

    __tablename__ = 'Keys'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    api_key = Column(String(64))
    secret_key = Column(String(64))

    def __repr__(self):
        return f'id={self.id}, api_key={self.api_key}, secret_key={self.secret_key}'

    def __str__(self):
        return f'id={self.id}'


class Transaction(Base):
    """
    Transaction info
    """

    __tablename__ = 'Transactions'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    bot_id = Column(ForeignKey('Bots.id', ondelete='CASCADE'))

    date = Column(DateTime())
    price = Column(DECIMAL(precision=32, scale=17))
    base_asset_balance = Column(DECIMAL(precision=32, scale=17))
    quote_asset_balance = Column(DECIMAL(precision=32, scale=17))
    base_asset_amount = Column(DECIMAL(precision=32, scale=17))
    quote_asset_amount = Column(DECIMAL(precision=32, scale=17))
    total_balance_in_quote_asset = Column(DECIMAL(precision=32, scale=17))
    type = Column(Enum(BotAction))
    money_mode = Column(Enum(BotMoneyMode))
