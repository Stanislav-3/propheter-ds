from sqlalchemy import ForeignKey, Column, String, Integer, CHAR, Text, LargeBinary, DateTime, DECIMAL
from config.settings import Base


class BotType(Base):
    """
    Implemented bot types.

    """

    __tablename__ = 'BotTypes'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    name = Column(String(100))
    description = Column(Text())

    def __repr__(self):
        return f'id={self.id}, name={self.name}'


class Bot(Base):
    """
    Implemented bots.

    """

    __tablename__ = 'Bots'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    stock_id = Column(ForeignKey('Stocks.id'))

    name = Column(String(100))
    description = Column(Text())

    some_general_attribute = Column(Text())

    def __repr__(self):
        return f'id={self.id}, name={self.name}, ' \
               f'some_general_attribute={self.some_general_attribute}'

    def __str__(self):
        return f'id={self.id}, name={self.name}'


class BotParametersType(Base):
    """
    Types of model parameters
    """

    __tablename__ = 'BotParametersTypes'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    bot_type_id = Column(ForeignKey('BotTypes.id'))

    name = Column(String(100))
    type = Column(String(20))

    def __repr__(self):
        return f'id={id}, name={self.name}, type={self.type}'

    def __str__(self):
        return f'{self.name}: {self.type}'


class BotParametersValue(Base):
    """
    Values of model parameters
    """

    __tablename__ = 'BotParametersValues'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    bot_id = Column(ForeignKey('Bots.id'))
    bot_parameters_type_id = Column(ForeignKey('BotParametersTypes.id'))

    value = Column(LargeBinary())

    def __repr__(self):
        return f'id={self.id}, bot_id={self.bot_id}, ' \
               f'bot_parameters_type_id={self.bot_parameters_type_id}, value={self.value}'

    def __str__(self):
        return f'id={self.id}, value={self.value}'


class Stock(Base):
    """
    Stocks data
    """

    __tablename__ = 'Stocks'

    id = Column(Integer, primary_key=True, index=True, unique=True)

    name = Column(String(32))
    dates = Column(DateTime())
    low = Column(DECIMAL(precision=12))
    high = Column(DECIMAL(precision=12))
    open = Column(DECIMAL(precision=12))
    close = Column(DECIMAL(precision=12))
    volume = Column(DECIMAL(precision=8))

    def __repr__(self):
        return f'id={self.id}, name={self.name}'

    def __str__(self):
        return f'id={self.id}, name={self.name}'
