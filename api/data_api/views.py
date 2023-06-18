from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from sqlalchemy.orm.session import Session
from pydantic import BaseModel
from datetime import datetime

from config.settings import get_db
from models.models_ import Stock, Kline


data_api_router = APIRouter(prefix='/data-api')


def parse_datetime(time: str) -> datetime:
    parse_str = '%Y-%m-%d %H:%M:%S.%f'

    try:
        date = datetime.strptime(time, parse_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f'Time {time} cannot be parsed with {parse_str}')

    return date


def parse_float(num: str) -> float:
    try:
        num = float(num)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f'Expected float, but get {num}')

    return num


def get_pair_id(pair_name: str, db: Session) -> int:
    pair = db.query(Stock).filter(Stock.name == pair_name).first()
    if pair is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f'Pair {pair_name} is not found in db')

    return pair.id


@data_api_router.post("/ticks")
async def new_ticks(pair: str = Form(...), time: str = Form(...), open: str = Form(...), close: str = Form(...),
                    high: str = Form(...), low: str = Form(...), vol: str = Form(...),
                    db: Session = Depends(get_db)):
    kline = Kline(stock_id=get_pair_id(pair, db), date=parse_datetime(time), low=parse_float(low),
                  high=parse_float(high), open=parse_float(open), close=parse_float(close), volume=parse_float(vol))

    db.add(kline)
    db.commit()
    return {'message': 'Successfully added new_tick'}
