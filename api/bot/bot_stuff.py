from typing import Literal, Type
from fastapi import status, HTTPException
from sqlalchemy.orm.session import Session

from pool.main import Pool
from algorithms.bots.trend_following import TrendFollowingBot
from algorithms.bots.dca import DCABot
from algorithms.bots.grid import GridBot
from algorithms.bots.reinforcement import ReinforcementBot
from api.bot.request_parameters import (TrendFollowingBotParameters, DCABotParameters,
                                        GridBotParameters, ReinforcementBotParameters)
from api.bot.validation import validate_bot_parameters_body
from api.bot.db_stuff import add_bot_to_db
from api.bot.data_api_stuff import register_pair, unregister_pair


def create_bot(BotClass, parameters: dict) -> TrendFollowingBot | DCABotParameters \
                                              | GridBotParameters | ReinforcementBotParameters:
    try:
        bot = BotClass(**parameters)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{e}')

    return bot


async def create_specific_bot(BotParameters: Type[TrendFollowingBotParameters | DCABotParameters
                                                  | GridBotParameters | ReinforcementBotParameters],
                              bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                              BotClass: Type[TrendFollowingBot | DCABot | GridBot | ReinforcementBot],
                              body: dict,
                              pool: Pool,
                              db: Session) -> int:
    parameters = validate_bot_parameters_body(BotParameters, body)

    pair_is_registered = await register_pair(parameters['pair'], db)

    bot_id = await add_bot_to_db(bot_type_name, parameters, db)
    parameters['id'] = bot_id

    try:
        bot = create_bot(BotClass, parameters)
    except (Exception, HTTPException) as e:
        if pair_is_registered:
            await unregister_pair(parameters['pair'], db)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Bot is not started. {e}')

    bot.start()
    pool.add(parameters['pair'], bot)

    return bot_id