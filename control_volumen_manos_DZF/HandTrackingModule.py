import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import os

class HandDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        
        # Initialize MediaPipe Tasks HandLandmarker
        base_options = python.BaseOptions(model_asset_path=os.path.join(os.path.dirname(__file__), 'hand_landmarker.task'))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.maxHands,
            min_hand_detection_confidence=self.detectionCon,
            min_hand_presence_confidence=self.trackCon,
            min_tracking_confidence=self.trackCon,
            running_mode=vision.RunningMode.IMAGE) # IMAGE mode is easier as it requires no timestamps
            
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        self.tipIds = [4, 8, 12, 16, 20] # Thumb, Index, Middle, Ring, Pinky
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),       # thumb
            (0, 5), (5, 6), (6, 7), (7, 8),       # index
            (0, 9), (9, 10), (10, 11), (11, 12),  # middle
            (0, 13), (13, 14), (14, 15), (15, 16),# ring
            (0, 17), (17, 18), (18, 19), (19, 20),# pinky
            (5, 9), (9, 13), (13, 17), (5, 17)    # palm
        ]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        
        self.results = self.detector.detect(mp_image)
        
        if self.results and self.results.hand_landmarks:
            for hand_landmarks in self.results.hand_landmarks:
                if draw:
                    h, w, c = img.shape
                    # Draw connections
                    for connection in self.HAND_CONNECTIONS:
                        p1 = hand_landmarks[connection[0]]
                        p2 = hand_landmarks[connection[1]]
                        x1, y1 = int(p1.x * w), int(p1.y * h)
                        x2, y2 = int(p2.x * w), int(p2.y * h)
                        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    # Draw landmarks
                    for lm in hand_landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(img, (cx, cy), 4, (0, 0, 255), cv2.FILLED)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []
        if self.results and self.results.hand_landmarks and len(self.results.hand_landmarks) > handNo:
            myHand = self.results.hand_landmarks[handNo]
            for id, lm in enumerate(myHand):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
            
            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax
            
            if draw:
                cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)
                
        return self.lmList, bbox

    def fingersUp(self):
        fingers = []
        if not self.lmList:
            return fingers
            
        # Thumb: compare x coordinates
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 Fingers: compare y coordinates
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]
