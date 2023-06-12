from fastapi import FastAPI, Request
from api.helloworld import hello_router
from api.bot import bot_router
from api.data_api import data_api_router


app = FastAPI()

app.include_router(hello_router)
app.include_router(bot_router)
app.include_router(data_api_router)
