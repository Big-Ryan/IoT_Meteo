from pydantic import BaseModel
from datetime import datetime

class CapteurCreate(BaseModel):
    sensor_id: str
    quartier: str
    latitude: float
    longitude: float
    actif: bool = True

class MesureCreate(BaseModel):
    sensor_id: str
    quartier: str
    temperature: float
    humidite: float
    pression: float

class MesureResponse(BaseModel):
    sensor_id: str
    timestamp: datetime
    quartier: str
    temperature: float
    humidite: float
    pression: float