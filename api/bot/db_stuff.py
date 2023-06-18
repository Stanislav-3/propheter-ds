from typing import Literal
from sqlalchemy.orm.session import Session
from models.models_ import Bot, BotType, Stock, Key, Kline, Transaction
from api.bot.request_parameters import BotBaseParameters


async def add_bot_to_db(bot_type_name: Literal['trend-following-bot', 'dca-bot', 'grid-bot', 'reinforcement-bot'],
                        parameters: dict,
                        db: Session) -> int:
    bot_type_id = db.query(BotType).filter(BotType.name == bot_type_name).first().id
    stock_id = db.query(Stock).filter(Stock.name == parameters['pair']).first().id

    bot = Bot(stock_id=stock_id,
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
              })

    db.add(bot)
    db.commit()

    return bot.id


async def add_pair_to_db(stock_name: str, db: Session) -> bool:
    if db.query(Stock).filter(Stock.name == stock_name).first():
        return False

    pair = Stock(name=stock_name)
    db.add(pair)
    db.commit()

    return True


async def remove_pair_and_klines_from_db(stock_name: str, db: Session) -> None:
    pair = db.query(Stock).filter(Stock.name == stock_name).first()
    if not pair:
        return

    db.delete(db.query(Kline).filter(Kline.stock_id == pair.id))
    db.delete(pair)
    db.commit()
