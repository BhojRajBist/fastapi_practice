from fastapi import FastAPI
from models import Base  # Import the Base class from models
from database import engine  # Import the engine from database

app = FastAPI()

@app.on_event("startup")
def startup_event():
    # Create the database tables
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/name/{name_id}")
async def name(name_id: int):
    return {"message": f"Hello {name_id}"}
