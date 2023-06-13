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
        self.return_type = ReturnType.LOG_RETURN
        self.hold_asset = False
        self.id = None

    @abstractmethod
    def start(self) -> None:
        self.status = BotStatus.LOADING

    @abstractmethod
    def stop(self) -> None:
        self.status = BotStatus.STOPPED

    @abstractmethod
    def step(self, new_price) -> BotEvaluationResult:
        if self.status != BotStatus.RUNNING:
            raise BotIsNotRunningError(f'You cannot use bot "{self.__class__.__name__}"'
                                       f'because it is still not configured')
        if self.money_mode == BotMoneyMode.NOT_CONFIGURED:
            raise BotModeIsNotConfiguredError(f'Mode of bot "{self.__class__.__name__}" is not configured')

        return BotEvaluationResult(action=BotAction.DO_NOTHING)

    def set_configured(self):
        self.status = BotStatus.RUNNING

        if self.money_mode == BotMoneyMode.NOT_CONFIGURED:
            raise BotModeIsNotConfiguredError(f'Mode of bot "{self.__class__.__name__}" is not configured')
