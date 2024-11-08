import pytest
import docker
import time
import redis
import os
from fastapi.testclient import TestClient
from unittest.mock import patch
from src import main
from src.utils import is_rtsp_link_working

@pytest.fixture(scope="session")
def redis_container():
    client = docker.from_env()
    
    container = client.containers.run(
        "redis:latest",
        detach=True,
        ports={"6379/tcp": "6379"}
    )

    time.sleep(5)  # Wait for Redis to be ready
    yield redis.Redis(host="localhost", port=6379, db=0)

    container.stop()

@pytest.fixture
def client(redis_container):
    from src.main import app
    with TestClient(app) as client:
        app.dependency_overrides[is_rtsp_link_working] = lambda url: True 
        yield client

def mock_is_rtsp_link_working(rtsp_url: str):
    return True

def mock_add_task(func, *args, **kwargs):
    return

# Test 1: Adding a parking lot with an invalid RTSP URL
def test_add_parking_lot_invalid_rtsp_url(client, redis_container):
    parking_lot_data = {
        "id": "1",
        "rstp_url": "rtsp://invalid_url"
    }

    response = client.post("/add_parking_lot/", json=parking_lot_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to capture frame from RTSP stream"}
    assert not redis_container.get("parking_lot:1")

# Test 2: Adding a parking lot with a valid RTSP URL
def test_add_parking_lot_valid_rtsp_url(client, redis_container, monkeypatch):
    monkeypatch.setattr(main, "is_rtsp_link_working", mock_is_rtsp_link_working)
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)

    parking_lot_data = {"id": "2", "rstp_url": "rtsp://valid_url"}
    response = client.post("/add_parking_lot/", json=parking_lot_data)
    assert response.status_code == 201
    assert response.json() == {"status": "Parking lot '2' added"}
    assert redis_container.get("parking_lot:2") == b"rtsp://valid_url"

# Test 3: Adding a parking lot that already exists
def test_add_parking_lot_already_exists(client, redis_container, monkeypatch):
    monkeypatch.setattr(main, "is_rtsp_link_working", mock_is_rtsp_link_working)
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)

    parking_lot_data = {"id": "2", "rstp_url": "rtsp://another_url"}
    response = client.post("/add_parking_lot/", json=parking_lot_data)
    assert response.status_code == 409
    assert response.json() == {"detail": "Parking lot already exists"}

# Test 4: Retrieving parking lot information
def test_get_parking_lot_info(client, redis_container):
    redis_container.set("parking_lot:3", "rtsp://test_url")
    redis_container.set("parking_lot:3:occupancy", '{"freed": 7, "occupied": 3, "total": 10}')

    response = client.get("/parking_lot/3")
    assert response.status_code == 200
    assert response.json() == {
        "parking_lot_id": "3",
        "image_url": "/images/3",
        "occupancy": {"freed": 7, "occupied": 3, "total": 10}
    }

# Test 5: Retrieving non-existent parking lot information
def test_get_parking_lot_info_not_found(client):
    response = client.get("/parking_lot/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Parking lot not found"}

# Test 6: Setting parking spots for a parking lot
def test_set_parking_spots(client, redis_container):
    redis_container.set("parking_lot:4", "rtsp://test_url")
    
    parking_spots = [
        {
            "name": "Spot A",
            "points": [(100, 100), (200, 200)]
        },
        {
            "name": "Spot B",
            "points": [(300, 300), (400, 400)]
        }
    ]

    response = client.post("/parking_lot/4/spots", json=parking_spots)
    assert response.status_code == 200
    assert response.json() == {"status": "Parking spots added to '4'"}

    saved_spots = redis_container.get("parking_lot:4:parking_spots")
    assert saved_spots is not None
    assert saved_spots == b'[{"name": "Spot A", "points": [[100, 100], [200, 200]]}, {"name": "Spot B", "points": [[300, 300], [400, 400]]}]'

# Test 7: Setting parking spots for a non-existent parking lot
def test_set_parking_spots_lot_not_found(client):
    parking_spots = [{"name": "Spot A", "points": [(100, 100), (200, 200)]}]
    response = client.post("/parking_lot/999/spots", json=parking_spots)
    assert response.status_code == 404
    assert response.json() == {"detail": "Parking lot not found"}

# Test 8: Serving an existing image
def test_serve_image(client):
    # Save a test image file
    os.makedirs("./images", exist_ok=True)
    test_image_path = "./images/5.png"
    with open(test_image_path, "wb") as f:
        f.write(b"test_image_data")

    response = client.get("/images/5.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Clean up
    os.remove(test_image_path)

# Test 9: Serving a non-existent image
def test_serve_image_not_found(client):
    response = client.get("/images/non_existent.png")
    assert response.status_code == 404
    assert response.json() == {"detail": "Image not found"}
