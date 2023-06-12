from fastapi import APIRouter


hello_router = APIRouter()


@hello_router.get('/')
def hello_world():
    return {'lala': 'Hello World!'}
