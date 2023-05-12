from sqlalchemy import ForeignKey, Column, String, Integer, CHAR, TEXT
from config.settings import Base


class Test(Base):
    __tablename__ = 'tests'

    id = Column(Integer, primary_key=True, index=True, unique=True)
    text = Column(TEXT)

    def __init__(self):
        pass

    def __repr__(self):
        pass
