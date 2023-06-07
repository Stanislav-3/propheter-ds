import asyncio
from api.helloworld import hello_world
from services.binance import BinanceAgent
from typing import Union
from fastapi import FastAPI
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/ticks/")
async def new_ticks(request):
    print('INFO: tick-tick')
    print('request: ', request)
    return {"Yas": "Gimme those ticks"}
