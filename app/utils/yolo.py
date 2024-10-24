import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO

model = YOLO('yolo11s.pt')

with open("coco.txt", "r") as coco_file:
    things = coco_file.read().split("\n")

def get_parking_info(rstp_url, parking_id, parking_spots):
    frames_to_skip = 15
    frame_num = 0
    cap = cv2.VideoCapture(rstp_url)
    
    occupied_spots = 0
    total_spots = 0

    if parking_id in parking_spots:
        total_spots = len(parking_spots[parking_id])

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.release()
            break

        frame_num += 1
        if frame_num < frames_to_skip:
            continue

        # Predict with YOLO
        results = model.predict(frame)
        a = results[0].boxes.data
        px = pd.DataFrame(a).astype("float")

        # Draw parking spots on the frame
        if parking_id in parking_spots:
            for spot in parking_spots[parking_id]:
                pts = np.array(spot['points'], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)  # Draw green polygons for spots

        occupied_spots = 0

        for index, row in px.iterrows():
            x1 = int(row[0])
            y1 = int(row[1])
            x2 = int(row[2])
            y2 = int(row[3])
            thing_id = int(row[5])
            thing = things[thing_id]
            
            if thing in ["truck", "car", "bus"]:
                cx = int((x1 + x2) // 2)
                cy = int((int((y1 + y2) // 2) + y2) // 2)
                cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)

                if parking_id in parking_spots:
                    for spot in parking_spots[parking_id]:
                        pts = np.array(spot['points'], np.int32)
                        if cv2.pointPolygonTest(pts, (cx, cy), False) >= 0:
                            cv2.polylines(frame, [pts], True, (0, 0, 255), 2)
                            occupied_spots += 1
                            break
        cap.release()
        return frame, occupied_spots, total_spots
