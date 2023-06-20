import requests
import logging
from fastapi import HTTPException
from sqlalchemy.orm.session import Session

from config.settings import DATA_API_URI
from api.bot.db_stuff import add_pair_to_db, remove_pair_and_klines_from_db


async def register_pair_on_data_api(pair: str, db: Session) -> None:
    logging.info(f'Try to register pair={pair} on data-api')

    response = requests.post(f'{DATA_API_URI}/api/add-pair/{pair}')
    if response.status_code != 200:
        await remove_pair_and_klines_from_db(pair, db)
        raise Exception(f'Post request to {DATA_API_URI}/api/add-pair/{pair} gave response '
                        f'with status_code={response.status_code}')

    logging.info(f'Successfully registered pair={pair}')


async def unregister_pair_on_data_api(pair: str, db: Session) -> None:
    logging.info(f'Try to unregister pair={pair} on data-api')

    response = requests.post(f'{DATA_API_URI}/api/remove-pair/{pair}')
    if response.status_code != 200:
        raise Exception(f'Post request to {DATA_API_URI}/api/remove-pair/{pair} gave response '
                        f'with status_code={response.status_code}')
