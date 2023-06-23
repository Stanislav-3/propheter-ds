from enum import Enum


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


class InvestmentIntervalScale(Enum):
    MINUTE = 'Minute'
    HOUR = 'Hour'
    DAY = 'Day'


class RunningMode(Enum):
    STATIC = 'Static'
    DYNAMIC = 'Dynamic'
