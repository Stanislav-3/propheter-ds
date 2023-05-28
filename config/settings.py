import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import dialect


load_dotenv(find_dotenv('.env', raise_error_if_not_found=True))

DEBUG = os.getenv('DEBUG')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_URI = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
API_KEY = os.getenv('API_KEY')  # 'XLO5wAwuQBafXwhbufPxGiRf1407VdDybfmA6rx0cveGzH0SovXZtfPnk6JR7m8F'
API_SECRET = os.getenv('API_SECRET')  # 'J0WIocYCYuwHRuPw38i0D4Z2s223qlOR6RkansCzdrD0LaUYqespiQy5tWPyS8Dj'


# db stuff
engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# engine = create_engine(
#     DATABASE_URI, connect_args={"check_same_thread": False}
# )
# database = databases.Database(SQLALCHEMY_DATABASE_URL)
Base: DeclarativeMeta = declarative_base()