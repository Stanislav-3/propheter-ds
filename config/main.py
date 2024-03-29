import logging

from fastapi import FastAPI
from api.bot.views import bot_router
from api.data_api.views import data_api_router


app = FastAPI()


@app.get('/hello')
async def hello():
    logging.info('hello view')
    return {'m': 'hello'}

app.include_router(bot_router)
app.include_router(data_api_router)
