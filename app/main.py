import asyncpg
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi import APIRouter
from pydantic import BaseModel
from database import connect_db


app = FastAPI()

@app.get("/")
def read_root():
    return {"Message" : "Welcome"}