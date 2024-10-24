from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import ParkingLot, ParkingSpot
from app.services.parking import add_parking_lot_service, set_parking_spots_service, get_parking_lot_info_service
from fastapi.responses import FileResponse
import os

router = APIRouter()

IMAGE_DIR = "parking_lot_images"

@router.post("/add_parking_lot/")
async def add_parking_lot(parking_lot: ParkingLot, background_tasks: BackgroundTasks):
    return await add_parking_lot_service(parking_lot, background_tasks)

@router.post("/parking_lot/{parking_id}/spots")
async def set_parking_spots(parking_id: str, spots: list[ParkingSpot]):
    return await set_parking_spots_service(parking_id, spots)

@router.get("/parking_lot/{parking_id}")
async def get_parking_lot_info(parking_id: str):
    return await get_parking_lot_info_service(parking_id)

@router.get("/images/{image_name}")
async def serve_image(image_name: str):
    image_path = os.path.join(IMAGE_DIR, image_name)
    
    if os.path.exists(image_path):
        return FileResponse(image_path, media_type="image/png")
    return {"error": "Image not found"}
