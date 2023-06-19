import requests
import logging
from fastapi import HTTPException
from sqlalchemy.orm.session import Session

from config.settings import DATA_API_URI
from api.bot.db_stuff import add_pair_to_db, remove_pair_and_klines_from_db


async def register_pair(pair: str, db: Session) -> bool:
    logging.info(f'Try to register pair={pair}')

    is_added = await add_pair_to_db(pair, db)
    if not is_added:
        logging.info(f'Pair={pair} is already registered')
        return False

    # Ticks are not being received yet
    response = requests.post(f'{DATA_API_URI}/api/add-pair/{pair}')
    if response.status_code != 200:
        await remove_pair_and_klines_from_db(pair, db)
        raise Exception(f'Post request to {DATA_API_URI}/api/add-pair/{pair} gave response '
                        f'with status_code={response.status_code}')

    logging.info(f'Successfully registered pair={pair}')
    return True


async def unregister_pair(pair: str, db: Session):
    logging.info(f'Unregister pair={pair}')

    await remove_pair_and_klines_from_db(pair, db)

    response = requests.post(f'{DATA_API_URI}/api/remove-pair/{pair}')
    if response.status_code != 200:
        raise Exception(f'Post request to {DATA_API_URI}/api/remove-pair/{pair} gave response '
                        f'with status_code={response.status_code}')