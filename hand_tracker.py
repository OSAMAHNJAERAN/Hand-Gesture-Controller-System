import os
import tempfile
import urllib.request
import cv2

class HandTracker:
    def __init__(self):
        # 0. MEDIAPIPE AI MODEL INITIALIZATION
        # CRITICAL FALLBACK: Change Working Directory to ASCII space to prevent C++ Crash
        original_cwd = os.getcwd()
        os.chdir(tempfile.gettempdir())

        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        model_path = 'hand_landmarker.task'
        if not os.path.exists(model_path):
            print("Downloading MediaPipe AI Hand Detection Model... Please wait.")
            urllib.request.urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task", 
                model_path
            )

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            running_mode=vision.RunningMode.IMAGE
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.mp = mp
        
        # Restore the original working directory
        os.chdir(original_cwd)

        # Hand Skeleton Connections mapping
        self.HAND_CONNECTIONS = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (5,9),(9,10),(10,11),(11,12),
            (9,13),(13,14),(14,15),(15,16),
            (13,17),(17,18),(18,19),(19,20),
            (0,17)
        ]

    def process_frame(self, img):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=imgRGB)
        
        results = self.detector.detect(mp_image)
        
        lmList = []
        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                for id, lm in enumerate(hand_landmarks):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append((id, cx, cy))

        return lmList

    def draw_landmarks(self, img, lmList):
        coords = [ (cx, cy) for (id, cx, cy) in lmList ]
        for (cx, cy) in coords:
            cv2.circle(img, (cx, cy), 4, (255, 0, 0), cv2.FILLED)
        
        for connection in self.HAND_CONNECTIONS:
            p1 = coords[connection[0]]
            p2 = coords[connection[1]]
            cv2.line(img, p1, p2, (200, 200, 200), 2)

class HandDetector:
    """
    A drop-in replacement for cvzone.HandTrackingModule.HandDetector
    that internally uses the modern MediaPipe Tasks API.
    """
    def __init__(self, detectionCon=0.8, maxHands=1):
        self.tracker = HandTracker()
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True, flipType=True):
        lmList_raw = self.tracker.process_frame(img)
        hands = []
        if lmList_raw:
            myLmList = []
            xList = []
            yList = []
            for id, cx, cy in lmList_raw:
                myLmList.append([cx, cy, 0])
                xList.append(cx)
                yList.append(cy)
                
            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            boxW, boxH = xmax - xmin, ymax - ymin
            bbox = xmin, ymin, boxW, boxH
            # Calculate center point
            cx, cy = bbox[0] + (bbox[2] // 2), bbox[1] + (bbox[3] // 2)
            
            # Simple heuristic for hand type
            handType = "Right"
            
            hand = {
                "lmList": myLmList,
                "bbox": bbox,
                "center": (cx, cy),
                "type": handType
            }
            hands.append(hand)
            
            if draw:
                self.tracker.draw_landmarks(img, lmList_raw)
                
        return hands, img

    def fingersUp(self, myHand):
        fingers = []
        myHandType = myHand["type"]
        myLmList = myHand["lmList"]
        
        # Thumb (Right hand)
        if myHandType == "Right":
            if myLmList[self.tipIds[0]][0] > myLmList[self.tipIds[0] - 1][0]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if myLmList[self.tipIds[0]][0] < myLmList[self.tipIds[0] - 1][0]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        # 4 Fingers
        for id in range(1, 5):
            if myLmList[self.tipIds[id]][1] < myLmList[self.tipIds[id] - 2][1]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers

