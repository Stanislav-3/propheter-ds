import asyncio
import json
from datetime import datetime
from binance import AsyncClient, Client, BinanceSocketManager, ThreadedWebsocketManager, ThreadedDepthCacheManager
from models.models_ import Stock
from config.settings import SessionLocal
from config.settings import API_KEY, API_SECRET


class BinanceAgent:
    def __init__(self):
        self.async_client = None

    async def start(self, stock_name: str):
        print(f'INFO: starting Binance agent for {stock_name}...')
        self.async_client = await AsyncClient.create()
        print(f'Client: {self.async_client}')
        bm = BinanceSocketManager(self.async_client)
        async with bm.kline_socket(symbol=stock_name) as stream:
            while True:
                res = await stream.recv()
                t = datetime.fromtimestamp(res.get('E') / 1000)
                k = res.get('k')
                o, c, h, l, v = [k.get(t) for t in ('o', 'c', 'h', 'l', 'v')]
                new_stock = Stock(
                    name=stock_name, dates=t,
                    open=o, close=c, high=h, low=l, volume=v
                )
                print(f'INFO: Binance-{stock_name} new stock: {new_stock}')
                db_session = SessionLocal()
                db_session.add(new_stock)
                db_session.commit()
        await self.async_client.close_connection()