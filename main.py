import os
import sys
import cv2
import numpy as np
import time
import math

# Use the local HandDetector because cvzone crashes on Python 3.13
from hand_tracker import HandDetector
from mouse_controller import MouseController

# Fix terminal encoding for Arabic paths
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Helper function to read images with Unicode (Arabic) paths
def imread_unicode(path):
    try:
        with open(path, "rb") as f:
            chunk = np.frombuffer(f.read(), dtype=np.uint8)
            return cv2.imdecode(chunk, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error reading image: {e}")
        return None

# Parameters
width, height = 1280, 720
gestureThreshold = 300
folderPath = "Presentation"

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Detectors and Controllers
detectorHand = HandDetector(detectionCon=0.8, maxHands=1)
mouseCtrl = MouseController(smoothing=4)

# Presentation Variables
imgList = []
delay = 30
buttonPressed = False
counter = 0
imgNumber = 0
annotations = [[]]
annotationNumber = -1
annotationStart = False
hs, ws = int(120 * 1), int(213 * 1)  # width and height of small image

# Smoothing variables for presentation drawing
prev_x, prev_y = 0, 0
smoothing = 5

# Modes State Machine
MODE_PRESENTATION = 0
MODE_MOUSE = 1
current_mode = MODE_PRESENTATION

mode_switched = False
mode_switch_time = 0

# Get list of presentation images
if not os.path.exists(folderPath):
    os.makedirs(folderPath)
pathImages = sorted(os.listdir(folderPath), key=len)
print(f"Loaded Slides: {pathImages}")

while True:
    # Get image frame
    success, img = cap.read()
    if not success:
        continue
    img = cv2.flip(img, 1)
    
    # Render Modes
    h_slide, w_slide = height, width
    imgCurrent = None
    
    if current_mode == MODE_PRESENTATION and pathImages:
        pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
        imgCurrent = imread_unicode(pathFullImage)
        if imgCurrent is None:
            imgCurrent = np.zeros((height, width, 3), dtype=np.uint8)
        h_slide, w_slide, _ = imgCurrent.shape

    # Find the hand and its landmarks
    hands, img = detectorHand.findHands(img)  # with draw
    
    # Draw Gesture Threshold line
    cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 5)

    # Display Current Mode
    mode_text = "MODE: PRESENTATION" if current_mode == MODE_PRESENTATION else "MODE: MOUSE"
    color = (255, 150, 0) if current_mode == MODE_PRESENTATION else (0, 255, 255)
    cv2.putText(img, mode_text, (20, 50), cv2.FONT_HERSHEY_DUPLEX, 1, color, 3)

    if hands and not buttonPressed:  # If hand is detected
        hand = hands[0]
        cx, cy = hand["center"]
        lmList = hand["lmList"]  # List of 21 Landmark points
        fingers = detectorHand.fingersUp(hand)  # List of which fingers are up

        # --- MODE SWITCHING LOGIC ---
        # Thumb and Pinky up -> Switch Mode (Hang loose / Call me gesture)
        if fingers == [1, 0, 0, 0, 1] and not mode_switched:
            if current_mode == MODE_PRESENTATION:
                current_mode = MODE_MOUSE
                # Hide the slides window so it doesn't get stuck on screen
                try:
                    cv2.destroyWindow("Slides")
                except:
                    pass
            else:
                current_mode = MODE_PRESENTATION
                
            mode_switched = True
            mode_switch_time = time.time()
            buttonPressed = True
            print(f"Switched to {mode_text}")
            continue # Skip processing other gestures this frame

        # --- PRESENTATION MODE LOGIC ---
        if current_mode == MODE_PRESENTATION and not mode_switched:
            # Constrain values for easier drawing
            xVal = int(np.interp(lmList[8][0], [width // 2, width], [0, w_slide]))
            yVal = int(np.interp(lmList[8][1], [150, height-150], [0, h_slide]))
            
            # Apply smoothing to reduce jitter
            if prev_x == 0 and prev_y == 0:
                prev_x, prev_y = xVal, yVal
            else:
                prev_x = prev_x + (xVal - prev_x) / smoothing
                prev_y = prev_y + (yVal - prev_y) / smoothing
                
            indexFinger = int(prev_x), int(prev_y)

            if cy <= gestureThreshold:  # If hand is at the height of the face
                if fingers == [1, 0, 0, 0, 0]:
                    print("Left (Prev Slide)")
                    buttonPressed = True
                    if imgNumber > 0:
                        imgNumber -= 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = False
                if fingers == [0, 0, 0, 0, 1]:
                    print("Right (Next Slide)")
                    buttonPressed = True
                    if imgNumber < len(pathImages) - 1:
                        imgNumber += 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = False

            if fingers == [0, 1, 1, 0, 0]:
                cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)
                annotationStart = False

            if fingers == [0, 1, 0, 0, 0]:
                if annotationStart is False:
                    annotationStart = True
                    annotationNumber += 1
                    annotations.append([])
                print(annotationNumber)
                annotations[annotationNumber].append(indexFinger)
                cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)
            else:
                annotationStart = False

            if fingers == [0, 1, 1, 1, 0]:
                if annotations:
                    if annotationNumber >= 0:
                        annotations.pop(-1)
                        annotationNumber -= 1
                        buttonPressed = True

            # Erase All
            if fingers == [1, 1, 1, 1, 1]:
                if annotations:
                    annotations = [[]]
                    annotationNumber = -1
                    annotationStart = False
                    buttonPressed = True

        # --- MOUSE MODE LOGIC ---
        elif current_mode == MODE_MOUSE and not mode_switched:
            # Constrain values to full screen resolution
            # We map a slightly larger area to the screen for ease of use
            xVal = int(np.interp(lmList[8][0], [width // 2 - 100, width], [0, mouseCtrl.screen_width]))
            yVal = int(np.interp(lmList[8][1], [100, height-100], [0, mouseCtrl.screen_height]))

            # Moving Mouse (Index finger up OR Index + Thumb up)
            if fingers == [0, 1, 0, 0, 0] or fingers == [1, 1, 0, 0, 0]:
                mouseCtrl.move_to(xVal, yVal)
                
            # Clicking (Distance between Index and Thumb)
            if fingers == [1, 1, 0, 0, 0] or fingers == [0, 1, 0, 0, 0]:
                x1, y1 = lmList[8][0], lmList[8][1]
                x2, y2 = lmList[4][0], lmList[4][1]
                length = math.hypot(x2 - x1, y2 - y1)
                
                is_pinched = (length < 40)
                mouseCtrl.evaluate_pinch(is_pinched)
                
                # Visual feedback for pinch on webcam
                if is_pinched:
                    cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
            else:
                mouseCtrl.evaluate_pinch(False)

            # Volume Control (3 Fingers up)
            if fingers == [0, 1, 1, 1, 0]:
                mouseCtrl.perform_volume_control(lmList[8][1])
                cv2.putText(img, "VOLUME CONTROL", (20, 100), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)
            else:
                mouseCtrl.reset_scroll()

    else:
        annotationStart = False
        prev_x, prev_y = 0, 0  # Reset smoothing when hand is lost
        if current_mode == MODE_MOUSE:
            mouseCtrl.evaluate_pinch(False)
            mouseCtrl.reset_scroll()

    # Debounce for regular buttons/gestures
    if buttonPressed:
        counter += 1
        if counter > delay:
            counter = 0
            buttonPressed = False

    # Debounce for mode switch (needs a time-based delay, not frame-based)
    if mode_switched and time.time() - mode_switch_time > 1.5:
        mode_switched = False

    # Draw annotations on Slide
    if current_mode == MODE_PRESENTATION and imgCurrent is not None:
        for i, annotation in enumerate(annotations):
            for j in range(len(annotation)):
                if j != 0:
                    cv2.line(imgCurrent, annotation[j - 1], annotation[j], (0, 0, 200), 12)

    # PiP Overlay and Show Windows
    if current_mode == MODE_PRESENTATION and imgCurrent is not None:
        imgSmall = cv2.resize(img, (ws, hs))
        imgCurrent[0:hs, w_slide - ws: w_slide] = imgSmall
        cv2.imshow("Slides", imgCurrent)

    cv2.imshow("Image", img)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
