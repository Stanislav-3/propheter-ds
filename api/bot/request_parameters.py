from typing import Literal, Dict, Optional, Type
from pydantic import BaseModel, parse_obj_as
from pydantic.error_wrappers import ValidationError
from datetime import datetime

from algorithms.bots.base import BotMoneyMode, ReturnType
from algorithms.bots.dca import InvestmentIntervalScale


class BotBaseParameters(BaseModel):
    min_level: float
    max_level: float
    max_money_to_invest: float
    pair: str

    key_id: Optional[int]

    money_mode: BotMoneyMode
    return_type: ReturnType


class TrendFollowingBotParameters(BotBaseParameters):
    slow_window: Optional[int]
    fast_window: Optional[int]


class DCABotParameters(BotBaseParameters):
    investment_money: float
    investment_interval: int
    investment_interval_scale: InvestmentIntervalScale


class GridBotParameters(BotBaseParameters):
    pass


class ReinforcementBotParameters(BotBaseParameters):
    pass
