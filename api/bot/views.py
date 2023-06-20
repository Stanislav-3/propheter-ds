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
from api.bot.data_api_stuff import try_to_register_pair, unregister_pair


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

    create_specific_bot_dict = {
        'trend-following-bot': create_specific_bot(TrendFollowingBotParameters, bot_type_name,
                                                   TrendFollowingBot, body, pool, db),
        'dca-bot': create_specific_bot(DCABotParameters, bot_type_name, DCABot, body, pool, db),
        'grid-bot': create_specific_bot(GridBotParameters, bot_type_name, GridBot, body, pool, db),
        'reinforcement-bot': create_specific_bot(ReinforcementBotParameters, bot_type_name,
                                                 ReinforcementBot, body, pool, db)
    }
    bot_id = await create_specific_bot_dict[bot_type_name]

    logging.info(f'Successfully created {bot_type_name} bot with id={bot_id}')
    return {'bot_id': bot_id, 'message': f'Bot with bot_type_name={bot_type_name} is successfully created'}


@bot_router.post("/start/{bot_id}")
async def start_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    logging.info(f'View start bot with id={bot_id}')

    # Start bot in db
    bot = db.query(Bot).get(bot_id)
    if not bot:
        logging.info(f'Bot with id={bot_id} is not found in the db')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Bot with id={bot_id} is not found in db. \n'
                                   f'In Pool bot={pool.get_bot(bot_id)}')

    bot.is_active = True
    db.commit()
    pair_id = bot.stock_id

    # Start bot in a pool
    pair = db.query(Stock).filter(Stock.id == pair_id).first().name
    is_started = pool.start_bot(pair, bot_id)
    if not is_started:
        logging.info(f'Bot with id={bot_id} is not found in the pool')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Bot with id={bot_id} is not found in pool')
    logging.info(f'Successfully started bot with id={bot_id} in pool')

    # Register pair if no bot is using it
    if db.query(Bot).filter(Bot.stock_id == pair_id).count() == 0:
        pair = db.query(Stock).filter(Stock.id == pair_id).first().name
        await unregister_pair(pair, db)
        logging.info(f'Successfully unregister pair with id={id} name={pair}')
    else:
        logging.info(f'Did not try to register pair with id={id}')

    logging.info(f'Bot with id={bot_id} is successfully started')
    return {'message': f'Bot with id={bot_id} is successfully started'}


@bot_router.post("/stop/{bot_id}")
async def stop_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    logging.info(f'View stop bot with id={bot_id}')

    # Stop bot in db
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        logging.info(f'Bot with id={bot_id} is not found in the db')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Bot with id={bot_id} is not found in db. \n'
                                   f'In Pool bot={pool.get_bot(bot_id)}')
    bot.is_active = False
    db.commit()
    pair_id = bot.stock_id
    logging.info(f'Successfully stopped bot with id={bot_id} in db')

    # Stop bot in a pool
    pair = db.query(Stock).filter(Stock.id == pair_id).first().name
    is_stopped = pool.stop_bot(pair, bot_id)
    if not is_stopped:
        logging.info(f'Bot with id={bot_id} is not found in the pool')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Bot with id={bot_id} is not found in pool')
    logging.info(f'Successfully stopped bot with id={bot_id} in pool')

    # Unregister pair if no bot is using it
    if db.query(Bot).filter(Bot.stock_id == pair_id)\
            .filter(Bot.is_active == True).count() == 0:
        pair = db.query(Stock).filter(Stock.id == pair_id).first().name
        await unregister_pair(pair, db)
        logging.info(f'Successfully unregister pair with id={pair_id} name={pair}')
    else:
        logging.info(f'Did not try to unregister pair with id={pair_id}')

    logging.info(f'Successfully stopped bot with id={bot_id}')
    return {'message': f'Bot with id={bot_id} is successfully stopped'}


@bot_router.post("/delete/{bot_id}")
async def delete_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    logging.info(f'View delete bot with id={bot_id}')

    # Delete bot from db
    bot = db.query(Bot).get(bot_id)
    if not bot:
        logging.info(f'Bot with id={bot_id} is not found in the db')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Bot with id={bot_id} is not found in db. \n'
                                   f'In Pool bot={pool.get_bot(bot_id)}')
    db.delete(bot)
    db.commit()
    pair_id = bot.stock_id
    logging.info(f'Successfully deleted bot with id={bot_id} from db')

    # Delete bot from Pool
    pair = db.query(Stock).filter(Stock.id == pair_id).first().name
    is_deleted = pool.remove(pair, bot_id)
    if not is_deleted:
        logging.info(f'Bot with id={bot_id} is not found in the pool')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Bot with id={bot_id} is not found in pool')
    logging.info(f'Successfully deleted bot with id={bot_id} from pool')

    # Unregister pair if no bot is using it
    if db.query(Bot).filter(Bot.stock_id == pair_id).count() == 0:
        await unregister_pair(pair, db)
        logging.info(f'Successfully unregister pair with id={pair_id} name={pair}')
    else:
        logging.info(f'Did not try to unregister pair with id={pair_id}')

    logging.info(f'Successfully deleted bot with id={bot_id}')
    return {'message': f'Successfully deleted bot with id={bot_id}'}
