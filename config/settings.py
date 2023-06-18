import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import dialect
from typing import Generator


load_dotenv(find_dotenv('.env', raise_error_if_not_found=True))

DEBUG = os.getenv('DEBUG')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_URI = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

DATA_API_URI = os.getenv('DATA_API_URI')


# Create an engine
engine = create_engine(DATABASE_URI)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)


# Function to get a new session
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base: DeclarativeMeta = declarative_base()
