from pydantic import BaseModel
from typing import List, Tuple

class ParkingSpot(BaseModel):
    points: List[Tuple[int, int]]  # List of points that form a polygon for the parking spot

class ParkingLot(BaseModel):
    parking_id: str
    rstp_url: str
