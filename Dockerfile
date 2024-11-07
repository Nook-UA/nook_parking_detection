FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src src
copy coco.txt .

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]
