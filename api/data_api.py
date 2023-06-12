from fastapi import APIRouter, Request


data_api_router = APIRouter()


@data_api_router.post("/api/ticks")
async def new_ticks(request: Request):
    return {"Yas": "Gimme those ticks"}