from typing import Type
from pydantic import parse_obj_as
from pydantic.error_wrappers import ValidationError
from fastapi import HTTPException, status
from api.bot.request_parameters import (TrendFollowingBotParameters, DCABotParameters,
                                        GridBotParameters, ReinforcementBotParameters)


def validate_bot_parameters_body(BotParameters: Type[TrendFollowingBotParameters | DCABotParameters
                                                     | GridBotParameters | ReinforcementBotParameters],
                                 body: dict) -> dict:
    try:
        parameters = parse_obj_as(BotParameters, body).dict()
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{e}')

    return parameters
