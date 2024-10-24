import os
import time
import json
import cv2
import numpy as np
from fastapi import BackgroundTasks
from app.utils.redis import r
from app.utils.yolo import get_parking_info
from app.models.schemas import ParkingLot, ParkingSpot

parking_lots = {}
parking_spots = {}

IMAGE_DIR = "parking_lot_images"
os.makedirs(IMAGE_DIR, exist_ok=True)
DELAY_BETWEEN_CHECKS = 10

async def add_parking_lot_service(parking_lot: ParkingLot, background_tasks: BackgroundTasks):
    if parking_lot.parking_id in parking_lots:
        return {"error": "Parking lot ID already exists"}

    parking_lots[parking_lot.parking_id] = parking_lot.rstp_url
    # Start background task for the parking lot
    background_tasks.add_task(capture_parking_info, parking_lot.parking_id, parking_lot.rstp_url)
    
    return {"status": f"Parking lot {parking_lot.parking_id} added and monitoring started."}

async def set_parking_spots_service(parking_id: str, spots: list[ParkingSpot]):
    if parking_id not in parking_lots:
        return {"error": "Parking lot not found"}

    parking_spots[parking_id] = [spot.dict() for spot in spots]
    return {"status": f"Parking spots for {parking_id} set successfully."}

async def get_parking_lot_info_service(parking_id: str):
    if parking_id not in parking_lots:
        return {"error": "Parking lot not found"}
    
    # Path to the saved image
    image_path = os.path.join(IMAGE_DIR, f"{parking_id}.png")
    
    if not os.path.exists(image_path):
        return {"error": "No image available yet for this parking lot"}
    
    # Generate a URL to serve the image
    image_url = f"/images/{parking_id}.png"
    
    # Fetch occupancy data from Redis
    occupancy_data = r.get(f"parking_lot:{parking_id}:occupancy")
    if occupancy_data:
        occupancy_data = json.loads(occupancy_data)
    else:
        occupancy_data = {"occupied": 0, "total": 0}

    return {
        "parking_lot_id": parking_id,
        "image_url": image_url,
        "occupancy": occupancy_data
    }

def capture_parking_info(parking_id, rstp_url):
    while True:
        frame, occupied_spots, total_spots = get_parking_info(rstp_url, parking_id, parking_spots)
        if frame is not None:
            image_path = os.path.join(IMAGE_DIR, f"{parking_id}.png")
            cv2.imwrite(image_path, frame)

            occupancy_data = {
                "freed": total_spots - occupied_spots,
                "occupied": occupied_spots,
                "total": total_spots
            }
            r.set(f"parking_lot:{parking_id}:occupancy", json.dumps(occupancy_data))

        time.sleep(DELAY_BETWEEN_CHECKS)
