import logging
from typing import Literal
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.exc import UnmappedInstanceError

from models.models_ import Bot, BotType, Stock, Key, Kline, Transaction
from api.bot.request_parameters import BotBaseParameters
from algorithms.bots.base import BotStatus


async def add_bot_to_db(bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                        parameters: dict,
                        db: Session) -> int:
    logging.info('Add bot to db')

    bot_type_id = db.query(BotType).filter(BotType.name == bot_type_name).first().id
    stock_id = db.query(Stock).filter(Stock.name == parameters['pair']).first().id

    bot = Bot(stock_id=stock_id,
              bot_type_id=bot_type_id,
              key_id=parameters['key_id'],
              status=BotStatus.LOADING,
              max_money_to_invest=parameters['max_money_to_invest'],
              max_level=parameters['max_level'],
              min_level=parameters['min_level'],
              return_type=parameters['return_type'],
              money_mode=parameters['money_mode'],
              parameters={
                  k: v for k, v in parameters.items() if k not in BotBaseParameters.__annotations__
              })

    db.add(bot)
    db.commit()

    return bot.id


async def add_pair_to_db(stock_name: str, db: Session) -> bool:
    logging.info(f'Try to add pair {stock_name} to db')

    existing_stock = db.query(Stock).filter(Stock.name == stock_name).first()
    logging.info(f'Existed stock: {existing_stock}')

    if existing_stock:
        logging.info(f'Pair {stock_name} already exists in db')
        return False

    pair = Stock(name=stock_name)
    db.add(pair)
    db.commit()

    logging.info(f'Successfully added pair {stock_name} to db')
    return True


async def remove_klines_from_db(stock_name: str, db: Session) -> None:
    logging.info(f'Remove klines of pair={stock_name} from db')

    pair = db.query(Stock).filter(Stock.name == stock_name).first()
    if not pair:
        logging.info(f'Pair {stock_name} doesn\'t exist in db')
        return

    db.query(Kline).filter(Kline.stock_id == pair.id).delete()
    db.commit()


async def remove_pair_and_klines_from_db(stock_name: str, db: Session) -> None:
    logging.info(f'Remove pair {stock_name} and its klines from db')

    pair = db.query(Stock).filter(Stock.name == stock_name).first()
    if not pair:
        logging.info(f'Pair {stock_name} doesn\'t exist in db')
        return

    db.query(Kline).filter(Kline.stock_id == pair.id).delete()
    db.delete(pair)
    db.commit()
