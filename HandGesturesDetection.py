import cv2
import numpy as np
import time
import autopy
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as pct

wCam,hCam = 640,480
frameR = 100 # frame reduction
smooththeing = 1 # smoothing factor


pTime = 0
plocX,plocY = 0,0
clocX,clocY=0,0

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=1)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

volume = cast(interface, POINTER(IAudioEndpointVolume))

print(volume.GetVolumeRange()) #==> (-63.5, 0.0, 0.5)
wScr, hScr = autopy.screen.size()
wScr, hScr = wScr-1, hScr-1


volumeRange = volume.GetVolumeRange()

minVol = volumeRange[0]
maxVol = volumeRange[1]
volBar = 400
vol = 0
volPer =0
area = 0
colorVol = (255,0,0)
bright = pct.get_brightness()[0]

while True: 
    #1. Find the hand landmarks
    success, img = cap.read()
    if(img is None):
        print("Can't receive frame (stream end?). Maybe issue with your camara. Exiting ...")
        break
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)
    
    #2 Get the tip of the index and middle fingers
    if len(lmList) != 0:
        area = (bbox[2]-bbox[0])*(bbox[3]-bbox[1])//100
        
        # print(x1, y1, x2, y2)
        #3 Check which fingers are up
        fingers = detector.fingersUp()
        print(fingers)
        #4 only index findet: Moving mode

        if all(element == 1 for element in fingers):
            
            bright = pct.get_brightness()[0]+10
            pct.set_brightness(bright)
            
        if all(element == 0 for element in fingers):
             bright = pct.get_brightness()[0]-10
             pct.set_brightness(bright)

        # Filter based on size
        if (250< area< 1000) and (fingers[0] == 1) and (fingers[1] == 1) and (fingers[2] == 0) and (fingers[3] == 0):

            # Find distance between index and thumb
            length, img, lineInfo = detector.findDistance(4,8,img)
            
            # Convert Volume
            volBar = np.interp(length,[50,240],[400,150])
            volPer = np.interp(length,[50,240],[0,100])
            # print(length,vol)    
            # Reduce Reolution to make it smoother
            smoothness = 5
            volPer = smoothness*round(volPer/smoothness)
            # Check fingers up 
            fingers = detector.fingersUp()
        
            # If Pinky is down set volume
            if not fingers[4]:
                volume.SetMasterVolumeLevelScalar(volPer/100,None)
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                colorVol = (0,255,0)
            else:
                colorVol = (255,0,255)
            
            #Hand range > 50-240
            #Volume > 63 - 0

        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        if (fingers[1] == 1) and (fingers[2] == 0) and (fingers[0] == 0) and (fingers[3] == 0) and (fingers[4] == 0):
            cv2.rectangle(img, (frameR,frameR),(wCam-frameR,hCam-frameR),(255,0,255),2)
            #5 Convert coordinates
            x3 = np.interp(x1,(frameR,wCam-frameR),(0,wScr))
            y3 = np.interp(y1,(frameR,hCam-frameR),(0,hScr))
            #6 Smoothen values
            clocX = plocX+(x3-plocX)/smooththeing
            clocY = plocY+(y3-plocY)/smooththeing
            #7 Move mouse
            # autopy.mouse.move(wScr-x3,y3)
            autopy.mouse.move(wScr-clocX,clocY)

            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plocX,plocX = clocX,clocY

        #8 Both Index and middle fingers are up: clicking mode
        if (fingers[1] == 1) and (fingers[2] == 1) and (fingers[0] == 0) and (fingers[3] == 0) and (fingers[4] == 0):
            cv2.rectangle(img, (frameR,frameR),(wCam-frameR,hCam-frameR),(255,0,255),2)
            length, img, lineInfo = detector.findDistance(8, 12, img)
        
            if length < 40:
                print(length)
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.click()
        
        
        #9 Find distance between fingers
        #10 Click mouse if distance is short
        
    
    # Drawings    
    cv2.rectangle(img, (50,150),(85,400),(255,0,0),3)
    cv2.rectangle(img, (50,int(volBar)),(85,400),(255,0,0),cv2.FILLED)
    cv2.putText(img, f"{int(volPer)} %", (40, 450), cv2.FONT_HERSHEY_PLAIN, 1.5,
                (255, 0, 0),3)
    cVol = int(volume.GetMasterVolumeLevelScalar()*100)
    cv2.putText(img, f"Volume: {int(cVol)}", (400, 50), cv2.FONT_HERSHEY_PLAIN, 1.5,
                colorVol,3)
    cv2.putText(img, f"Brightness: {int(bright)}%", (400, 100), cv2.FONT_HERSHEY_PLAIN, 1.5,
                (255, 0, 0),3)


    #11 Frame Rate
    cTime = time.time() 
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f"FPS: {int(fps)}", (20, 50), cv2.FONT_HERSHEY_PLAIN, 1.5,
                (255, 0, 0),3)
    #12 Display

    cv2.imshow("img", img)
    cv2.waitKey(1)
