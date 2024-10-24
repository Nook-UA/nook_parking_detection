# How to run

- Start a docker container for a RTSP server:
    - `docker run --rm -it -v $PWD/rtsp-simple-server.yml:/rtsp-simple-server.yml -p 8554:8554 aler9/rtsp-simple-server`

- Start streaming the video using ffmpeg:
    - `./stream.sh`

- Run the python script:
    - Create the enviroment and install the requirements
        - `python -m venv venv`
        - `source venv/bin/activate`
        - `pip install -r requirements.txt`
    - Run the program:
        - `uvicorn app.main:app --reload`