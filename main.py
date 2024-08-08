from fastapi import Depends, HTTPException, status,FastAPI
from models import Base 
from database import engine ,SessionLocal
from pydantic import BaseModel
import models

app = FastAPI()

db = SessionLocal()
# @app.on_event("startup")
# def startup_event():
#     Base.metadata.create_all(bind=engine)

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# @app.get("/name/{name_id}")
# async def name(name_id: int):
#     return {"message": f"Hello {name_id}"}


class OurBaseModel(BaseModel):
    class Config:
        orm_mode= True


class Person(OurBaseModel):
    id : int
    firstn : str
    lastn : str
    isMale : bool


@app.get("/",response_model=list[Person])
def get_AllPersons():
    get_AllPersons= db.query(models.Person).all()
    return get_AllPersons


@app.post("/addPerson",response_model=Person)
def add_Person(person:Person):
    print(person)
    newPerson = models.Person(
        id = person.id,
        firstn = person.firstn,
        lastn = person.lastn,
        isMale = person.isMale
    )

    find_person = db.query(models.Person).filter(models.Person.id == person.id).first()

    if find_person is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Person with this ID already exists")
    db.add(newPerson)
    db.commit()

    return newPerson
