from typing import Literal, Dict, Optional, Type
import requests
from fastapi import APIRouter, Request, Response, Depends, status, HTTPException, Form, Body
from pydantic import BaseModel, parse_obj_as
from pydantic.error_wrappers import ValidationError
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.session import Session

from models.models_ import Bot, BotType, Stock, Key, Kline, Transaction
from config.settings import get_db
from pool.main import Pool, get_pool
from algorithms.bots.trend_following import TrendFollowingBot
from algorithms.bots.dca import DCABot
from algorithms.bots.grid import GridBot
from algorithms.bots.reinforcement import ReinforcementBot
from api.bot.request_parameters import (
    BotBaseParameters, TrendFollowingBotParameters, DCABotParameters, GridBotParameters, ReinforcementBotParameters
)
from config.settings import DATA_API_URI


bot_router = APIRouter(prefix='/bot')


def validate_body(BotParameters: Type[TrendFollowingBotParameters | DCABotParameters
                                      | GridBotParameters | ReinforcementBotParameters],
                  body: dict) -> dict:
    try:
        parameters = parse_obj_as(BotParameters, body).dict()
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{e}')

    return parameters


def create_bot(BotClass, parameters: dict) -> TrendFollowingBot:
    try:
        bot = BotClass(**parameters)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{e}')

    return bot


async def save_bot_to_db(bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                         parameters: dict,
                         db: Session) -> int:
    bot_type_id = db.query(BotType).filter(BotType.name == bot_type_name).first().id
    stock_id = db.query(Stock).filter(Stock.name == parameters['pair']).first().id

    bot = Bot(
        stock_id=stock_id,
        bot_type_id=bot_type_id,
        key_id=parameters['key_id'],
        is_active=True,
        max_money_to_invest=parameters['max_money_to_invest'],
        max_level=parameters['max_level'],
        min_level=parameters['min_level'],
        return_type=parameters['return_type'],
        money_mode=parameters['money_mode'],
        parameters={
            k: v for k, v in parameters.items() if k not in BotBaseParameters.__annotations__
        }
    )

    db.add(bot)
    db.commit()

    return bot.id


async def try_to_add_pair_to_db(stock_name: str, db: Session) -> bool:
    if db.query(Stock).filter(Stock.name == stock_name):
        return False

    pair = Stock(name=stock_name)
    db.add(pair)
    db.commit()

    return True


async def remove_pair_from_db(stock_name: str, db: Session) -> bool:
    pair = db.query(Stock).filter(Stock.name == stock_name).first()

    if not pair:
        return False
    # pair_id = pair.id
    # maybe add logic for deleting klines

    db.delete(pair)
    db.commit()

    return True


async def register_pair(pair: str, db: Session) -> bool:
    pair_added = await try_to_add_pair_to_db(pair, db)
    if not pair_added:
        return False

    response = requests.post(f'{DATA_API_URI}/api/add-pair/{pair}')
    if response.status_code != 200:
        await remove_pair_from_db(pair, db)
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])

    return True


async def unregister_pair(pair: str, db: Session):
    removed = await remove_pair_from_db(pair, db)
    if not removed:
        raise HTTPException(status_code=500, detail=f'Pair {pair} is not found in db')

    response = requests.post(f'{DATA_API_URI}/api/remove-pair/{pair}')
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])


async def create_specific_bot(BotParameters: Type[TrendFollowingBotParameters | DCABotParameters
                                                  | GridBotParameters | ReinforcementBotParameters],
                              bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                              BotClass: Type[TrendFollowingBot | DCABot | GridBot | ReinforcementBot],
                              body: dict,
                              pool: Pool,
                              db: Session) -> int:
    parameters = validate_body(BotParameters, body)

    registered = await register_pair(parameters['pair'], db)

    bot_id = await save_bot_to_db(bot_type_name, parameters, db)
    parameters['id'] = bot_id

    try:
        bot = create_bot(BotClass, parameters)
    except Exception as e:
        if registered:
            await unregister_pair(parameters['pair'], db)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Bot is not started\n{e}')

    bot.start()
    pool.add(parameters['pair'], bot)

    return bot_id


@bot_router.post("/create/{bot_type_name}")
async def create_bot(request: Request,
                     bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                     pool: Pool = Depends(get_pool),
                     db: Session = Depends(get_db)):
    body = dict(await request.form())

    if bot_type_name == 'trend-following-bot':
        bot_id = await create_specific_bot(TrendFollowingBotParameters, bot_type_name, TrendFollowingBot, body, pool, db)
    elif bot_type_name == 'dca-bot':
        bot_id = await create_specific_bot(DCABotParameters, bot_type_name, DCABot, body, pool, db)
    elif bot_type_name == 'grid-bot':
        bot_id = await create_specific_bot(GridBotParameters, bot_type_name, GridBot, body, pool, db)
    elif bot_type_name == 'reinforcement-bot':
        bot_id = await create_specific_bot(ReinforcementBotParameters, bot_type_name, ReinforcementBot, body, pool, db)
    else:
        raise ValueError(f'Unknown bot_type_name={bot_type_name}')

    return {'bot_id': bot_id, 'message': f'Bot with bot_type_name={bot_type_name} is successfully created'}


# TODO: NOT TO ADD DCA BOT TO RAM
@bot_router.post("/start/{bot_id}")
async def start_bot(bot_id: int, pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    errors_detail = []
    errors_detail_separator = '\n'

    bot = db.query(Bot).get(bot_id)
    try:
        bot.is_active = True
        db.commit()
    except UnmappedInstanceError:
        errors_detail.append(f'Bot with id={bot_id} is not found in the database')

    bot = pool.get_bot(bot_id)
    if bot:
        bot.start()
    else:
        errors_detail.append(f'Bot with id={bot_id} is not found in the pool')

    if errors_detail:
        raise HTTPException(404, detail=errors_detail_separator.join(errors_detail))
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
