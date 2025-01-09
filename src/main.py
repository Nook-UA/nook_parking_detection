import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter
from fastapi.responses import FileResponse
from src.schemas import ParkingLot, ParkingSpot
from src.utils import get_parking_info, is_rtsp_link_working

import redis
import os
import cv2
import json
import time

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

IMAGE_DIR = "./images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

DELAY_BETWEEN_CHECKS = 10

class BackgroundRunner:
    def __init__(self):
        pass
    
    async def start_parking_lot_service(self, parking_lot: ParkingLot):
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
            else:
                occupancy_data = {
                    "ERROR": "Cannot access the RTSP URL"
                }
                
            db.set(f"parking_lot:{parking_lot.id}:occupancy", json.dumps(occupancy_data))
            await asyncio.sleep(DELAY_BETWEEN_CHECKS)

runner = BackgroundRunner()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On application startup, query Redis for all parking lots and start background tasks for each
    for key in db.scan_iter("parking_lot:*"):
        parking_lot_id = key.decode().split(":")[1]
        parking_lot_url = db.get(f"parking_lot:{parking_lot_id}")
        if parking_lot_url:
            parking_lot = ParkingLot(id=parking_lot_id, rstp_url=parking_lot_url.decode())
            asyncio.create_task(runner.start_parking_lot_service(parking_lot))
    yield
    
router = APIRouter(prefix='/parking-detection')

@router.get("/health", status_code=200)
async def check_health():
    return {"status": f"healthy"}

@router.post("/add_parking_lot", status_code=201)
async def add_parking_lot(parking_lot: ParkingLot, background_tasks: BackgroundTasks):
    if db.get(f"parking_lot:{parking_lot.id}"):
        raise HTTPException(status_code=409, detail="Parking lot already exists")

    if not is_rtsp_link_working(parking_lot.rstp_url):
        raise HTTPException(status_code=400, detail="Failed to capture frame from RTSP stream")

    db.set(f"parking_lot:{parking_lot.id}", parking_lot.rstp_url)

    asyncio.create_task(runner.start_parking_lot_service(parking_lot))

    return {"status": f"Parking lot '{parking_lot.id}' added"}

@router.get("/parking_lot/{parking_lot_id}", status_code=200)
async def get_parking_lot_info(parking_lot_id: str):
    if not db.get(f"parking_lot:{parking_lot_id}"):
        raise HTTPException(status_code=404, detail="Parking lot not found")

    occupancy = json.loads(db.get(f"parking_lot:{parking_lot_id}:occupancy"))

    return {
        "parking_lot_id": parking_lot_id,
        "image_url": f"/images/{parking_lot_id}.png",
        "occupancy": occupancy
    }

@router.post("/parking_lot/{parking_lot_id}/spots")
async def set_parking_spots(parking_lot_id: str, spots: list[ParkingSpot]):
    if not db.get(f"parking_lot:{parking_lot_id}"):
        raise HTTPException(status_code=404, detail="Parking lot not found")
    
    # convert the ParkingSpots to dicts to be able to store them in redis
    spots = [spot.model_dump() for spot in spots]
    db.set(f"parking_lot:{parking_lot_id}:parking_spots", json.dumps(spots))

    return {"status": f"Parking spots added to '{parking_lot_id}'"}

@router.get("/images/{image_name}")
async def serve_image(image_name: str):
    image_path = os.path.join(IMAGE_DIR, image_name)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")

app = FastAPI(lifespan=lifespan)
app.include_router(router)