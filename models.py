from database import Base,engine
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text

def create_tables():
    Base.metadata.create_all(engine)


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer,primary_key=True)
    firstn = Column(String(40),nullable=False)
    lastn = Column(String(40),nullable=False)
    isMale = Column(Boolean)