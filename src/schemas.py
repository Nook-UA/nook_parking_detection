from pydantic import BaseModel
from typing import List, Tuple
from json import JSONEncoder

class ParkingSpot(BaseModel):
    name: str
    points: List[Tuple[float, float]]  

class ParkingLot(BaseModel):
    id: str
    rstp_url: str
