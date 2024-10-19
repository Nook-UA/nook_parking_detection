#!/bin/bash

# Default video file
DEFAULT_VIDEO="parking.mp4"

# Check if an argument is provided
if [ $# -eq 1 ]; then
    VIDEO_FILE="$1"
else
    VIDEO_FILE="$DEFAULT_VIDEO"
fi

# Check if the video file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "Error: No video file found. Please provide a valid video file or ensure $DEFAULT_VIDEO exists."
    exit 1
fi

# Run the ffmpeg command with the selected video file
ffmpeg -re -stream_loop -1 -i "$VIDEO_FILE" -f rtsp -b:v 1000K -rtsp_transport tcp rtsp://localhost:8554/live.stream
