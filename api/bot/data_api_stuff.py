import requests
import logging
from fastapi import HTTPException
from sqlalchemy.orm.session import Session

from config.settings import DATA_API_URI
from api.bot.db_stuff import add_pair_to_db, remove_pair_and_klines_from_db


async def try_to_register_pair(pair: str, db: Session) -> bool:
    logging.info(f'Try to register pair={pair}')

    is_newly_registered = await add_pair_to_db(pair, db)
    if not is_newly_registered:
        logging.info(f'Pair={pair} is already registered')
        return False

    # Register pair on data api
    response = requests.post(f'{DATA_API_URI}/api/add-pair/{pair}')
    if response.status_code != 200:
        await remove_pair_and_klines_from_db(pair, db)
        raise Exception(f'Post request to {DATA_API_URI}/api/add-pair/{pair} gave response '
                        f'with status_code={response.status_code}')

    logging.info(f'Successfully registered pair={pair}')
    return True


async def unregister_pair(pair: str, db: Session):
    logging.info(f'Try to unregister pair={pair}')

    await remove_pair_and_klines_from_db(pair, db)

    response = requests.post(f'{DATA_API_URI}/api/remove-pair/{pair}')
    if response.status_code != 200:
        raise Exception(f'Post request to {DATA_API_URI}/api/remove-pair/{pair} gave response '
                        f'with status_code={response.status_code}')


async def unregister_only_pair_on_dataapi(pair: str):
    logging.info(f'Try to unregister only pair={pair} on dataapi')

    response = requests.post(f'{DATA_API_URI}/api/remove-pair/{pair}')
    if response.status_code != 200:
        raise Exception(f'Post request to {DATA_API_URI}/api/remove-pair/{pair} gave response '
                        f'with status_code={response.status_code}')