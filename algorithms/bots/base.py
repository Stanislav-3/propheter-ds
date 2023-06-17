from abc import ABC, abstractmethod
from enum import Enum
from exceptions.bot_exceptions import BotIsNotRunningError, BotModeIsNotConfiguredError
from typing import NamedTuple


class BotStatus(Enum):
    LOADING = 'Loading'
    RUNNING = 'Running'
    STOPPED = 'Stopped'


class BotAction(Enum):
    BUY = 'Buy'
    HOLD = 'Hold'
    SELL = 'Sell'
    DO_NOTHING = 'Do nothing'


class BotMoneyMode(Enum):
    REAL = 'Real'
    PAPER = 'Paper'
    NOT_CONFIGURED = 'Not configured'


class BotEvaluationResult(NamedTuple):
    action: BotAction


class ReturnType(Enum):
    LOG_RETURN = 'Log_return'
    RETURN = 'Return'


class BotBase(ABC):
    def __init__(self):
        self.status = BotStatus.STOPPED
        self.money_mode = BotMoneyMode.NOT_CONFIGURED

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

    def buy(self):
        if self.money_mode == BotMoneyMode.PAPER:
            pass
        elif self.money_mode == BotMoneyMode.REAL:
            # todo: add transaction to db an request to data api
            pass

    def sell(self):
        if self.money_mode == BotMoneyMode.PAPER:
            pass
        elif self.money_mode == BotMoneyMode.REAL:
            # todo: add transaction to db an request to data api
            pass