import logging

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from sqlalchemy.orm.session import Session
from pydantic import BaseModel
from datetime import datetime
from binance import AsyncClient
from binance.exceptions import BinanceAPIException

from config.settings import get_db
from models.models_ import Stock, Kline, Key
from pool.main import Pool, get_pool
from api.data_api.preprocessing import split_pair, float_to_str


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
                    pool: Pool = Depends(get_pool),
                    db: Session = Depends(get_db)):
    # Adding new tick to db
    kline = Kline(stock_id=get_pair_id(pair, db), date=parse_datetime(time), low=parse_float(low),
                  high=parse_float(high), open=parse_float(open), close=parse_float(close), volume=parse_float(vol))

    db.add(kline)
    db.commit()

    # Wake up models
    pool.run_bots(pair, parse_float(close))

    return {'message': 'Successfully added new_tick and run bots'}


def get_balance(currency: str, account_info) -> float | None:
    for balance in account_info['balances']:
        if balance['asset'] == currency:
            return float(balance['free'])

    return None


# @data_api_router.post('/buy/{pair}')
# async def buy_pair(pair: str,
#                    key_id: int = Form(...),
#                    quote_asset_quantity: float = Form(...),
#                    db: Session = Depends(get_db)):
#     logging.info(f'View sell pair={pair}, quote_asset_quantity={quote_asset_quantity}')
#
#     key = db.query(Key).get(key_id)
#     if not key:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f'Key with id={key_id} is not found')
#
#     client = await AsyncClient.create(api_key=key.api_key, api_secret=key.secret_key)
#
#     base_currency, quote_currency = split_pair(pair)
#     quote_balance = get_balance(quote_currency, await client.get_account())
#     buy_amount = min(quote_balance, quote_asset_quantity)
#
#     order = await client.order_market_buy(symbol=pair, quoteOrderQty=float_to_str(buy_amount))
#
#     await client.close_connection()
#
#     fills = order['fills'][0]
#
#     return {
#         'message': 'Successfully sell',
#         'base_asset_bought': float(fills['qty']) - float(fills['commission']),
#         'quote_asset_sold': float(order['cummulativeQuoteQty']),
#         'price': float(fills['price'])
#     }
#
#
# @data_api_router.post('/sell/{pair}')
# async def sell_pair(pair: str,
#                     key_id: int = Form(...),
#                     quote_asset_quantity: float = Form(...),
#                     db: Session = Depends(get_db)):
#     logging.info(f'View sell pair={pair}, quote_asset_quantity={quote_asset_quantity}')
#
#     key = db.query(Key).get(key_id)
#     if not key:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f'Key with id={key_id} is not found')
#
#     client = await AsyncClient.create(api_key=key.api_key, api_secret=key.secret_key)
#
#     base_currency, quote_currency = split_pair(pair)
#     base_balance = get_balance(base_currency, await client.get_account())
#
#     try:
#         order = await client.order_market_sell(symbol=pair, quoteOrderQty=float_to_str(quote_asset_quantity))
#     except BinanceAPIException:
#         order = await client.order_market_sell(symbol=pair, quantity=float_to_str(base_balance))
#
#     await client.close_connection()
#
#     fills = order['fills'][0]
#
#     return {
#         'message': 'Successfully sell',
#         'base_asset_sold': float(fills['qty']),
#         'quote_asset_bought': float(order['cummulativeQuoteQty']) - float(fills['commission']),
#         'price': float(fills['price'])
#     }
