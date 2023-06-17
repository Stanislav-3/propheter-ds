from typing import Literal, Dict, Optional, Type
from pydantic import BaseModel, parse_obj_as
from pydantic.error_wrappers import ValidationError

from algorithms.bots.base import BotMoneyMode, ReturnType


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
    investment_interval: int


class GridBotParameters(BotBaseParameters):
    pass


class ReinforcementBotParameters(BotBaseParameters):
    pass
