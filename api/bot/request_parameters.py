from typing import Optional
from pydantic import BaseModel

from algorithms.bots.base import BotMoneyMode, ReturnType
from algorithms.bots.dca import InvestmentIntervalScale
from algorithms.bots.grid import RunningMode


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
    money_to_trade: float
    levels_amount: int
    running_mode: RunningMode
    boundary_factor: Optional[float]


class ReinforcementBotParameters(BotBaseParameters):
    pass


bot_type_bot_parameters_mapping = {
    'trend-following-bot': TrendFollowingBotParameters,
    'dca-bot': DCABotParameters,
    'grid-bot': GridBotParameters,
    'reinforcement-bot': ReinforcementBotParameters
}


def parse_part_of_parameters(bot_type_name: str, body: dict) -> dict:
    parameters = bot_type_bot_parameters_mapping[bot_type_name].__annotations__
    parameters.update(BotBaseParameters.__annotations__)

    parsed_body = {}
    for key, value in body.items():
        value_type = parameters.get(key)
        if value_type is None:
            raise ValueError(f'Incorrect parameters. There is no parameter {key} in BotParameters')

        parsed_body[key] = value_type(value)

    return parsed_body


