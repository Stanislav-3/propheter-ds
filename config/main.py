import asyncio
from api.helloworld import hello_world
from services.binance import BinanceAgent
from typing import Union
from fastapi import FastAPI, Request
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/ticks")
async def new_ticks(request: Request):
    return {"Yas": "Gimme those ticks"}


@app.post("/start-bot/{bot_type_name}")
async def start_bot(request: Request,  bot_type_name: int):
    return {'bot_id': bot_id}
