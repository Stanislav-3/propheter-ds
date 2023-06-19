import logging
from typing import Literal, Type
from fastapi import APIRouter, Request, Depends, status, HTTPException
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.session import Session

from models.models_ import Bot, BotType, Stock, Key, Kline, Transaction
from pool.main import Pool, get_pool
from algorithms.bots.trend_following import TrendFollowingBot
from algorithms.bots.dca import DCABot
from algorithms.bots.grid import GridBot
from algorithms.bots.reinforcement import ReinforcementBot
from config.settings import get_db
from api.bot.request_parameters import (TrendFollowingBotParameters,
                                        DCABotParameters, GridBotParameters, ReinforcementBotParameters)
from api.bot.bot_stuff import create_specific_bot
from api.bot.db_stuff import activate_bot


bot_router = APIRouter(prefix='/bot')


@bot_router.get('/exc')
async def raise_exception():
    raise Exception(30 * 'THIS IS THE EXCEPTION!!!!!!!!!!!!!!!\n')


@bot_router.post("/create/{bot_type_name}")
async def create_bot(request: Request,
                     bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                     pool: Pool = Depends(get_pool),
                     db: Session = Depends(get_db)):
    logging.info(f'Create bot view | bot_type_name={bot_type_name}')
    body = dict(await request.form())

    if bot_type_name == 'trend-following-bot':
        bot_id = await create_specific_bot(TrendFollowingBotParameters, bot_type_name,
                                           TrendFollowingBot, body, pool, db)
    elif bot_type_name == 'dca-bot':
        bot_id = await create_specific_bot(DCABotParameters, bot_type_name, DCABot, body, pool, db)
    elif bot_type_name == 'grid-bot':
        bot_id = await create_specific_bot(GridBotParameters, bot_type_name, GridBot, body, pool, db)
    elif bot_type_name == 'reinforcement-bot':
        bot_id = await create_specific_bot(ReinforcementBotParameters, bot_type_name,
                                           ReinforcementBot, body, pool, db)
    else:
        raise ValueError(f'Unknown bot_type_name={bot_type_name}')

    logging.info(f'Successfully created {bot_type_name} bot with id={bot_id}')

    return {'bot_id': bot_id, 'message': f'Bot with bot_type_name={bot_type_name} is successfully created'}


@bot_router.post("/start/{bot_id}")
async def start_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    try:
        await activate_bot(bot_id, db)

        bot = pool.get_bot(bot_id)
        # start_bot_and_register_pair(bot, pool, pair, db)
    except (Exception, UnmappedInstanceError, HTTPException) as e:
        raise HTTPException(404, detail=str(e))

    return {'message': f'Bot with id={bot_id} is successfully started'}


# todo: think of logic when some inconsistency happened (and could it really happen? should it be considered then?)
@bot_router.post("/stop/{bot_id}")
async def stop_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    errors_detail = []
    errors_detail_separator = '\n'

    bot = db.query(Bot).get(bot_id)
    try:
        bot.is_active = False
        db.commit()
    except UnmappedInstanceError:
        errors_detail.append(f'Bot with id={bot_id} is not found in the database')

    bot = pool.get_bot(bot_id)
    if bot:
        bot.stop()
    else:
        errors_detail.append(f'Bot with id={bot_id} is not found in the pool')

    if errors_detail:
        raise HTTPException(404, detail=errors_detail_separator.join(errors_detail))

    return {'message': f'Bot with id={bot_id} is successfully stopped'}


# TODO: async session for sqlalchemy?
# TODO: ADD DELETING OF PAIR IF NO BOTS ARE USING IT
@bot_router.post("/delete/{bot_id}")
async def delete_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    errors_detail = []
    errors_detail_separator = '\n'

    bot = db.query(Bot).get(bot_id)
    try:
        db.delete(bot)
        db.commit()
    except UnmappedInstanceError:
        errors_detail.append(f'Bot with id={bot_id} is not found in the database')

    bot = pool.get_bot(bot_id)
    if bot:
        del bot
    else:
        errors_detail.append(f'Bot with id={bot_id} is not found in the pool')

    if errors_detail:
        raise HTTPException(404, detail=errors_detail_separator.join(errors_detail))

    return {'message': f'Bot with id={bot_id} is successfully deleted'}
