from typing import Optional, Union
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

    fast_min: Optional[int]
    fast_max: Optional[int]
    slow_max: Optional[int]
    fast_slow_min_delta: Optional[int]


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

        try:
            # if Optional argument
            if value_type.__origin__ is Union:
                # if NoneType
                if value == 'None' or value is None:
                    parsed_body[key] = None
                else:
                    # if not a NonType
                    parsed_body[key] = value_type.__args__[0](value)
        except AttributeError:
            # if not optional argument
            parsed_body[key] = value_type(value)

    return parsed_body
