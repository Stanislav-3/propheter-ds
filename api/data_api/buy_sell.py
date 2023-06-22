import logging

from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from datetime import datetime
from binance import AsyncClient
from binance.exceptions import BinanceAPIException

from models.models_ import Stock, Kline, Key
from api.data_api.preprocessing import split_pair, float_to_str


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


def get_balance(currency: str, account_info) -> float | None:
    for balance in account_info['balances']:
        if balance['asset'] == currency:
            return float(balance['free'])

    return None


async def buy_pair(pair: str, key_id: int, quote_asset_quantity: float, db: Session):
    logging.info(f'View sell pair={pair}, quote_asset_quantity={quote_asset_quantity}')

    key = db.query(Key).get(key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Key with id={key_id} is not found')

    client = await AsyncClient.create(api_key=key.api_key, api_secret=key.secret_key)

    base_currency, quote_currency = split_pair(pair)
    quote_balance = get_balance(quote_currency, await client.get_account())
    buy_amount = min(quote_balance, quote_asset_quantity)

    order = await client.order_market_buy(symbol=pair, quoteOrderQty=float_to_str(buy_amount))

    await client.close_connection()

    fills = order['fills'][0]

    return {
        'message': 'Successfully sell',
        'base_asset_bought': float(fills['qty']) - float(fills['commission']),
        'quote_asset_sold': float(order['cummulativeQuoteQty']),
        'price': float(fills['price'])
    }


async def sell_pair(pair: str, key_id: int, quote_asset_quantity: float, db: Session):
    logging.info(f'View sell pair={pair}, quote_asset_quantity={quote_asset_quantity}')

    key = db.query(Key).get(key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Key with id={key_id} is not found')

    client = await AsyncClient.create(api_key=key.api_key, api_secret=key.secret_key)

    base_currency, quote_currency = split_pair(pair)
    base_balance = get_balance(base_currency, await client.get_account())

    try:
        order = await client.order_market_sell(symbol=pair, quoteOrderQty=float_to_str(quote_asset_quantity))
    except BinanceAPIException:
        order = await client.order_market_sell(symbol=pair, quantity=float_to_str(base_balance))

    await client.close_connection()

    fills = order['fills'][0]

    return {
        'message': 'Successfully sell',
        'base_asset_sold': float(fills['qty']),
        'quote_asset_bought': float(order['cummulativeQuoteQty']) - float(fills['commission']),
        'price': float(fills['price'])
    }
