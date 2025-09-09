from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId
from typing import Optional, List
import os

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

origins = [
    'http://localhost:3000',
    'https://project1-auto.vercel.app'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


# database

class Car(BaseModel):
    id: str = Field(alias="_id")
    make: str
    model: str
    year: int
    color: Optional[str] = None
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

client = MongoClient(os.environ.get('DB_URL'))

db = client['cars']
collection = db['cars']

@app.get('/cars')
async def get_cars(
    make: Optional[str] = Query(None, description="Filter by car make"),
    model: Optional[str] = Query(None, description="Filter by car model"),
    year: Optional[int] = Query(None, description="Filter by manufacturing year"),
    fuel: Optional[str] = Query(None, description="Filter by fuel type"),
    limit: int = Query(10, ge=1, le=100, description="Limit number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):

    try:
        filter_dict = {}

        if make:
            filter_dict['make'] = {"$regex": make, "$options": "i"}

        if model:
            filter_dict['model'] = {"$regex" : model, "$options" : "i"}

        if fuel:
            filter_dict['fuel_type'] = {"$regex": fuel, "$options": "i"}

        if year:
            filter_dict['year'] = year

        documents = collection.find(filter_dict).limit(limit).skip(skip)

        cars = []
        for document in documents:
            document["_id"] = str(document["_id"])
            cars.append(document)

        return cars

    except OperationFailure as e:
        raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occured: {str(e)}")