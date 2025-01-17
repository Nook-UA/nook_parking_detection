# How to run

## Manually

- Start a docker container for a RTSP server:
    - `docker run --rm -it -v $PWD/rtsp-simple-server.yml:/rtsp-simple-server.yml -p 8554:8554 aler9/rtsp-simple-server`

- Start streaming the video using ffmpeg:
    - `./stream.sh`

- Run an Redis server:
    - `redis-server`

- Run the python script:
    - Create the enviroment and install the requirements
        - `python -m venv venv`
        - `source venv/bin/activate`
        - `pip install -r requirements.txt`
    - Run the program:
        - `uvicorn src.main:app --reload`

## Docker

- Run the docker compose:
    - `docker-compose up --build`

- Stream the video:
    - `./stream.sh`

# Tests

- To run the tests make sure you are inside the venv and use:
    - `source venv/bin/activate`
    - `python -m pytest`