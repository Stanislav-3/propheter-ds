from fastapi import APIRouter, Request, Response, Depends, status, HTTPException
from models.models_ import Bot
from sqlalchemy.orm import Session
from config.settings import get_db, SessionLocal
from sqlalchemy.orm.exc import UnmappedInstanceError
from pool.main import Pool, get_pool


bot_router = APIRouter(prefix='/bot')


@bot_router.post("/start-new/{bot_type_name}")
async def start_new_bot(request: Request,  bot_type_name: str):
    return {'bot_type_name': bot_type_name}


@bot_router.post("/start/{bot_id}")
async def start_bot(bot_id: int):
    return {'bot_type_name': bot_id}


@bot_router.post("/stop/{bot_id}")
async def stop_bot(bot_id: int, pool: Pool = Depends(get_pool)):
    return {}


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
