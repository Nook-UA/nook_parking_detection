import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
import time

TIME_BETWEEN_FRAMES = 5

model=YOLO('yolo11s.pt')

coco = open("coco.txt", "r")
things = coco.read().split("\n")

cap=cv2.VideoCapture('rtsp://localhost:8554/live.stream')

start = None
while True:    
    ret,frame = cap.read()
    if not ret:
        break
    
    # only work every X seconds
    if not start: start = time.time()
    end = time.time()
    if (end - start) < TIME_BETWEEN_FRAMES: 
        continue
    else:
        start = None

    results=model.predict(frame)

    a=results[0].boxes.data
    px=pd.DataFrame(a).astype("float") 
    for index,row in px.iterrows():
        
        x1=int(row[0])
        y1=int(row[1])
        x2=int(row[2])
        y2=int(row[3])
        thing_id=int(row[5])
        thing=things[thing_id]
        
        if thing in ["truck", "car", "bus"]:

            # get the center of the vehicle
            cx=int(x1+x2)//2 
            cy=int(y1+y2)//2

            # put a red circle on the detected vehicles
            cv2.circle(frame,(cx,cy),3,(0,0,255),-1)
      
            # results9=cv2.pointPolygonTest(np.array(area9,np.int32),((cx,cy)),False)
            # if results9>=0:
            #    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
            #    cv2.circle(frame,(cx,cy),3,(0,0,255),-1)
            #    list9.append(c)  

    cv2.imshow("parking", frame)

    if cv2.waitKey(1)&0xFF==27:
            break

cap.release()
cv2.destroyAllWindows()
#stream.stop()

