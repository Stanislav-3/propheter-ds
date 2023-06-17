from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm.session import Session
from pydantic import BaseModel
from datetime import datetime

from config.settings import get_db
from models.models_ import Stock, Kline


data_api_router = APIRouter(prefix='/data-api')


@data_api_router.post("/ticks")
async def new_ticks(pair: str = Form(...), time: str = Form(...), open: str = Form(...), close: str = Form(...),
                    high: str = Form(...), low: str = Form(...), vol: str = Form(...),
                    db: Session = Depends(get_db)):
    print(time)
    pair = db.query(Stock).filter(Stock.name == pair).first()
    if pair is None:
        pass

    db.add(
        Kline(stock_id=pair.id, date=datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f"), low=float(low), high=float(high),
              open=float(open), close=float(close), volume=float(vol))
    )
    db.commit()
    return {'time': time}
