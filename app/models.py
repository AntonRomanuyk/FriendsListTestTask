from database import Base
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String


class Friend(Base):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    profession = Column(String, nullable=False)
    profession_description  = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
