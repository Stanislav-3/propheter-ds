from fastapi import APIRouter, Request, Response, Depends, status, HTTPException, Form, Body
from models.models_ import Bot
from config.settings import get_db, SessionLocal
from sqlalchemy.orm.exc import UnmappedInstanceError
from pool.main import Pool, get_pool
from typing import Literal, Dict, Optional, Type
from pydantic import BaseModel, parse_obj_as
from algorithms.bots.base import BotMoneyMode, ReturnType
from algorithms.bots.trend_following import TrendFollowingBot
from algorithms.bots.dca import DCABot
from algorithms.bots.grid import GridBot
from algorithms.bots.reinforcement import ReinforcementBot
from pydantic.error_wrappers import ValidationError
# todo: understand the difference
# from sqlalchemy.orm import Session
from sqlalchemy.orm.session import Session

bot_router = APIRouter(prefix='/bot')


class BotBaseParameters(BaseModel):
    money_mode: BotMoneyMode
    return_type: ReturnType
    stock: str
    max_level: float
    min_level: float


class TrendFollowingBotParameters(BotBaseParameters):
    slow_sma: Optional[int]
    fast_sma: Optional[int]


class DCABotParameters(BotBaseParameters):
    pass


class GridBotParameters(BotBaseParameters):
    pass


class ReinforcementBotParameters(BotBaseParameters):
    pass


async def create_specific_bot(BotParameters: Type[TrendFollowingBotParameters | DCABotParameters
                                                  | GridBotParameters | ReinforcementBotParameters],
                              Bot: Type[TrendFollowingBot | DCABot | GridBot | ReinforcementBot],
                              body: dict, pool: Pool, db: Session):
    try:
        parameters = parse_obj_as(BotParameters, body)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{e}')
    try:
        bot = TrendFollowingBot(**parameters.dict())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{e}')

    # bot.start()
    # pool.add(body['stock'], bot)

    # db.add(Bot(is_active=True, ))
    # db.commit()


@bot_router.post("/create/{bot_type_name}")
async def create_bot(request: Request,
                     bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                     pool: Pool = Depends(get_pool), db: Session = Depends(get_db)):
    body = dict(await request.form())

    if bot_type_name == 'trend-following-bot':
        await create_specific_bot(TrendFollowingBotParameters, TrendFollowingBot, body, pool, db)
    elif bot_type_name == 'dca-bot':
        await create_specific_bot(DCABotParameters, DCABot, body, pool, db)
    elif bot_type_name == 'grid-bot':
        await create_specific_bot(GridBotParameters, GridBot, body, pool, db)
    elif bot_type_name == 'reinforcement-bot':
        await create_specific_bot(ReinforcementBotParameters, ReinforcementBot, body, pool, db)
    else:
        raise ValueError(f'Unknown bot_type_name={bot_type_name}')

    return {'message': f'Bot with bot_type_name={bot_type_name} is successfully created'}


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
