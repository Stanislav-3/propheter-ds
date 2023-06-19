from typing import Type
from pydantic import parse_obj_as
from pydantic.error_wrappers import ValidationError
from api.bot.request_parameters import (TrendFollowingBotParameters, DCABotParameters,
                                        GridBotParameters, ReinforcementBotParameters)


def validate_bot_parameters_body(BotParameters: Type[TrendFollowingBotParameters | DCABotParameters
                                                     | GridBotParameters | ReinforcementBotParameters],
                                 body: dict) -> dict:
    try:
        parameters = parse_obj_as(BotParameters, body).dict()
    except ValidationError as e:
        raise ValueError(str(e))

    return parameters
