from fastapi import APIRouter, Request, Response, Depends, status, HTTPException
from models.models_ import Bot
from sqlalchemy.orm import Session
from config.settings import get_db, SessionLocal
from sqlalchemy.orm.exc import UnmappedInstanceError


bot_router = APIRouter(prefix='/bot')


@bot_router.post("/start-new/{bot_type_name}")
async def start_new_bot(request: Request,  bot_type_name: str):
    return {'bot_type_name': bot_type_name}


@bot_router.post("/start/{bot_id}")
async def start_bot(bot_id: int):
    return {'bot_type_name': bot_id}


@bot_router.post("/stop/{bot_id}")
async def stop_bot(bot_id: int):
    return {}


@bot_router.post("/delete/{bot_id}")
async def delete_bot(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).get(bot_id)
    try:
        db.delete(bot)
    except UnmappedInstanceError:
        raise HTTPException(404, detail=f'Bot with id={bot_id} is not found')

    db.commit()
    return {'message': f'Bot with id={bot_id} is successfully deleted'}
