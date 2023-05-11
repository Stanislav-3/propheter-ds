import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv('.env', raise_error_if_not_found=True))

DEBUG = os.getenv('DEBUG')
