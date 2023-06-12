from fastapi import APIRouter, Request


bot_router = APIRouter()


@bot_router.post("/start-bot/{bot_type_name}")
async def start_bot(request: Request,  bot_type_name: str):
    return {'bot_type_name': bot_type_name}