import logging
from typing import Literal, Type
from fastapi import APIRouter, Request, Depends, status, HTTPException
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.session import Session

from models.models_ import Bot, BotType, Stock, Key, Kline, Transaction
from pool.main import Pool, get_pool
from algorithms.bots.base import BotStatus
from algorithms.bots.trend_following import TrendFollowingBot
from algorithms.bots.dca import DCABot
from algorithms.bots.grid import GridBot
from algorithms.bots.reinforcement import ReinforcementBot
from config.settings import get_db
from api.bot.request_parameters import (TrendFollowingBotParameters,
                                        DCABotParameters, GridBotParameters, ReinforcementBotParameters,
                                        parse_part_of_parameters)
from api.bot.bot_stuff import create_specific_bot
from api.bot.data_api_stuff import register_pair_on_data_api, unregister_pair_on_data_api
from api.bot.db_stuff import remove_klines_from_db, remove_pair_and_klines_from_db


bot_router = APIRouter(prefix='/bot')


@bot_router.get('/get-bot-status/{bot_id}')
async def get_bot_status(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).get(bot_id)
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Bot with id={bot_id} is not found in db')

    return {
        'bot_status': bot.status,
        'message': f'Bot status for bot with id={bot_id} is successfully obtained'
    }


@bot_router.get('/get-bot-parameters-schema/{bot_id}')
async def get_bot_parameters_schema(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).get(bot_id)
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Bot with id={bot_id} is not found in db')

    bot_type = db.query(BotType).get(bot.bot_type_id)

    return {
        'bot_parameters_schema': bot_type.parameters_schema,
        'message': f'Bot parameters for bot with id={bot_id} is successfully obtained'
    }


@bot_router.get('/get-bot-transactions/{bot_id}')
async def get_bot_transactions(bot_id: int, db: Session = Depends(get_db)):
    transactions = db.query(Transaction)\
        .filter(Transaction.bot_id == bot_id)\
        .order_by(Transaction.date).all()

    return {'transactions': transactions}


@bot_router.put('/edit/{bot_id}')
async def edit_bot(request: Request, bot_id: int,
                   pool: Pool = Depends(get_pool),
                   db: Session = Depends(get_db)):
    logging.info(f'View edit bot with id={bot_id}')
    # Stop bot
    await stop_bot(bot_id)

    bot_db = db.query(Bot).get(bot_id)
    bot_type_id = bot_db.bot_type_id
    bot_type_name = db.query(BotType).get(bot_type_id).name

    # Get body
    body = dict(await request.form())

    # Parse body
    try:
        parsed_body = parse_part_of_parameters(bot_type_name, body)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # Update bot in the pool
    bot = pool.get_bot(bot_id)
    bot.__dict__.update(parsed_body)

    # Update bot in db todo: cannot change pair of bot
    bot_param_field = {}
    bot_other_fields = {}
    for key, value in parsed_body.items():
        if key in ['min_level', 'max_level', 'max_money_to_invest', 'money_mode', 'return_type']:
            bot_other_fields[key] = value
        else:
            bot_other_fields[key] = value

    bot_db.__dict__.update(bot_other_fields)
    bot_db.parameters.__dict__.update(bot_param_field)
    db.commit()

    # Start bot
    await start_bot(bot_id)

    return {'message': f'Successfully edited bot with id={bot_id}'}


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

    bot.status = BotStatus.LOADING
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

    # Register pair if no other bot is using it
    if db.query(Bot).filter(Bot.stock_id == pair_id)\
            .filter(Bot.status != BotStatus.STOPPED).count() == 1:
        pair = db.query(Stock).filter(Stock.id == pair_id).first().name
        await register_pair_on_data_api(pair)
        logging.info(f'Successfully register pair with id={id} name={pair}')
    else:
        logging.info(f'Did not try to unregister pair with id={id}')

    logging.info(f'Bot with id={bot_id} is successfully started')
    return {'message': f'Bot with id={bot_id} is successfully started'}


@bot_router.post("/stop/{bot_id}")
async def stop_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    logging.info(f'View stop bot with id={bot_id}')

    # Stop bot in db
    bot = db.query(Bot).get(bot_id)
    if not bot:
        logging.info(f'Bot with id={bot_id} is not found in the db')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Bot with id={bot_id} is not found in db. \n'
                                   f'In Pool bot={pool.get_bot(bot_id)}')
    bot.status = BotStatus.STOPPED
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
            .filter(Bot.status != BotStatus.STOPPED).count() == 0:
        pair = db.query(Stock).filter(Stock.id == pair_id).first().name
        await remove_klines_from_db(pair, db)
        await unregister_pair_on_data_api(pair)
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
        await unregister_pair_on_data_api(pair)
        await remove_pair_and_klines_from_db(pair, db)
        logging.info(f'Successfully unregister pair with id={pair_id} name={pair}')
    else:
        logging.info(f'Did not try to unregister pair with id={pair_id}')

    logging.info(f'Successfully deleted bot with id={bot_id}')
    return {'message': f'Successfully deleted bot with id={bot_id}'}
