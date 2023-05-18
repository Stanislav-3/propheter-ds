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


class BotMode(Enum):
    REAL = 'Real'
    PAPER = 'Paper'
    NOT_CONFIGURED = 'Not configured'


class BotEvaluationResult(NamedTuple):
    action: BotAction


class BotBase(ABC):
    def __init__(self):
        self.status = BotStatus.STOPPED
        self.mode = BotMode.NOT_CONFIGURED

    @abstractmethod
    def start(self) -> None:
        self.status = BotStatus.LOADING

    @abstractmethod
    def stop(self) -> None:
        self.status = BotStatus.STOPPED

    @abstractmethod
    def evaluate(self) -> BotEvaluationResult:
        if self.status != BotStatus.RUNNING:
            raise BotIsNotRunningError(f'You cannot use bot "{self.__class__.__name__}"'
                                       f'because it is still not configured')
        if self.mode == BotMode.NOT_CONFIGURED:
            raise BotModeIsNotConfiguredError(f'Mode of bot "{self.__class__.__name__}" is not configured')

        return BotEvaluationResult(action=BotAction.DO_NOTHING)

    def set_configured(self):
        self.status = BotStatus.RUNNING

        if self.mode == BotMode.NOT_CONFIGURED:
            raise BotModeIsNotConfiguredError(f'Mode of bot "{self.__class__.__name__}" is not configured')
