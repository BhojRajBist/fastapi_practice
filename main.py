from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}



@app.get("/name/{name_id}")
async def name(name_id):
    return {f"Hello {name_id}"}
