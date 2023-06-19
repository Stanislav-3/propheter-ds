import logging
from typing import Literal, Type
from fastapi import status, HTTPException
from sqlalchemy.orm.session import Session

from models.models_ import Bot
from pool.main import Pool
from algorithms.bots.trend_following import TrendFollowingBot
from algorithms.bots.dca import DCABot
from algorithms.bots.grid import GridBot
from algorithms.bots.reinforcement import ReinforcementBot
from api.bot.request_parameters import (TrendFollowingBotParameters, DCABotParameters,
                                        GridBotParameters, ReinforcementBotParameters)
from api.bot.validation import validate_bot_parameters_body
from api.bot.db_stuff import add_bot_to_db
from api.bot.data_api_stuff import try_to_register_pair, unregister_pair


async def create_specific_bot(BotParameters: Type[TrendFollowingBotParameters | DCABotParameters
                                                  | GridBotParameters | ReinforcementBotParameters],
                              bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                              BotClass: Type[TrendFollowingBot | DCABot | GridBot | ReinforcementBot],
                              body: dict,
                              pool: Pool,
                              db: Session) -> int:
    logging.info(f'Try to create specific {bot_type_name} bot')

    # Validate body
    parameters = validate_bot_parameters_body(BotParameters, body)

    # Register pair if it's not registered yet
    await try_to_register_pair(parameters['pair'], db)

    # Add bot to db
    bot_id = await add_bot_to_db(bot_type_name, parameters, db)
    parameters['id'] = bot_id

    # Create bot
    bot = BotClass(**parameters)
    bot.start()

    # Adding bot to Pool
    pool.add(parameters['pair'], bot)

    return bot_id
