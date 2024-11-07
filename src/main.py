from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from src.schemas import ParkingLot, ParkingSpot
from src.utils import get_parking_info

import redis
import os
import cv2
import json
import time

db = redis.Redis(host='localhost', port=6379, db=0)

IMAGE_DIR = "./images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

DELAY_BETWEEN_CHECKS = 10

app = FastAPI()

def start_parking_lot_service(parking_lot: ParkingLot):
    while True:

        parking_spots = db.get(f"parking_lot:{parking_lot.id}:parking_spots")
        if parking_spots:
            parking_spots = json.loads(parking_spots)
        else:
            parking_spots = None

        frame, occupied_spots, total_spots = get_parking_info(parking_lot.rstp_url, parking_spots)
        if frame is not None:
            image_path = os.path.join(IMAGE_DIR, f"{parking_lot.id}.png")
            cv2.imwrite(image_path, frame)

            occupancy_data = {
                "freed": total_spots - occupied_spots,
                "occupied": occupied_spots,
                "total": total_spots
            }

            db.set(f"parking_lot:{parking_lot.id}:occupancy", json.dumps(occupancy_data))

        time.sleep(DELAY_BETWEEN_CHECKS)

@app.post("/add_parking_lot/", status_code=201)
async def add_parking_lot(parking_lot: ParkingLot, background_tasks: BackgroundTasks):

    if db.get(f"parking_lot:{parking_lot.id}"):
        raise HTTPException(status_code=409, detail="Parking lot already exists")

    db.set(f"parking_lot:{parking_lot.id}", parking_lot.rstp_url)

    background_tasks.add_task(start_parking_lot_service, parking_lot)

    return {"status": f"Parking lot '{parking_lot.id}' added"}

@app.get("/parking_lot/{parking_lot_id}", status_code=200)
async def get_parking_lot_info(parking_lot_id: str):
    
    if not db.get(f"parking_lot:{parking_lot_id}"):
        raise HTTPException(status_code=404, detail="Parking lot not found")

    occupancy = json.loads(db.get(f"parking_lot:{parking_lot_id}:occupancy"))

    return {
        "parking_lot_id": parking_lot_id,
        "image_url": f"/images/{parking_lot_id}",
        "occupancy": occupancy
    }

@app.post("/parking_lot/{parking_lot_id}/spots")
async def set_parking_spots(parking_lot_id: str, spots: list[ParkingSpot]):

    if not db.get(f"parking_lot:{parking_lot_id}"):
        raise HTTPException(status_code=404, detail="Parking lot not found")
    
    # convert the ParkingSpots to dicts to be able to store them in redis
    spots = [spot.dict() for spot in spots]
    db.set(f"parking_lot:{parking_lot_id}:parking_spots", json.dumps(spots))

    return {"status": f"Parking spots added to '{parking_lot_id}'"}

@app.get("/images/{image_name}")
async def serve_image(image_name: str):
    image_path = os.path.join(IMAGE_DIR, image_name)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")