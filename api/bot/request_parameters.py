from typing import Literal, Dict, Optional, Type
from pydantic import BaseModel, parse_obj_as
from pydantic.error_wrappers import ValidationError

from algorithms.bots.base import BotMoneyMode, ReturnType


class BotBaseParameters(BaseModel):
    min_level: float
    max_level: float
    max_money_to_invest: float
    stock: str

    key_id: Optional[int]

    money_mode: BotMoneyMode
    return_type: ReturnType


class TrendFollowingBotParameters(BotBaseParameters):
    slow_sma: Optional[int]
    fast_sma: Optional[int]


class DCABotParameters(BotBaseParameters):
    pass


class GridBotParameters(BotBaseParameters):
    pass


class ReinforcementBotParameters(BotBaseParameters):
    pass
