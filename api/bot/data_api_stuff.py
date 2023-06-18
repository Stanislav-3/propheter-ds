import requests
from fastapi import HTTPException
from sqlalchemy.orm.session import Session

from config.settings import DATA_API_URI
from api.bot.db_stuff import add_pair_to_db, remove_pair_and_klines_from_db


async def register_pair(pair: str, db: Session) -> bool:
    is_added = await add_pair_to_db(pair, db)
    if not is_added:
        return False

    # Ticks are not being received yet
    response = requests.post(f'{DATA_API_URI}/api/add-pair/{pair}')
    if response.status_code != 200:
        await remove_pair_and_klines_from_db(pair, db)
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])

    return True


async def unregister_pair(pair: str, db: Session):
    await remove_pair_and_klines_from_db(pair, db)

    response = requests.post(f'{DATA_API_URI}/api/remove-pair/{pair}')
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()['detail'])