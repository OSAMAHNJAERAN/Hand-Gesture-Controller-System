"""
=============================================================================
  Hand Gesture Controlled Presentation
=============================================================================
  Controls:
    Thumb up  [1,0,0,0,0]  → Previous slide
    Pinky up  [0,0,0,0,1]  → Next slide
    Index     [0,1,0,0,0]  → Draw on slide
    Index+Mid [0,1,1,0,0]  → Laser pointer (no drawing saved)
    3 fingers [0,1,1,1,0]  → Undo last drawing stroke
    'q' key                → Quit
=============================================================================
"""

import os
import cv2
import numpy as np
from hand_tracker import HandDetector

# ──────────────────────────── CONFIGURATION ────────────────────────────

# Camera resolution
width, height = 1280, 720

# Presentation folder (must contain .png slides: 1.png, 2.png, ...)
PRESENTATION_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Presentation")

# PiP (Picture-in-Picture) dimensions
PIP_WIDTH  = 213
PIP_HEIGHT = 120

# Gesture threshold — hand must be above this Y line to trigger navigation
gestureThreshold = 300

# Debounce settings — prevents rapid repeated gesture activation
buttonDelay = 30

# Drawing style
DRAW_COLOR     = (0, 0, 200)   # BGR – red-ish
DRAW_THICKNESS = 12
POINTER_COLOR  = (0, 0, 255)   # BGR – pure red
POINTER_RADIUS = 12


def main():
    # ──────────────────────── STEP 1: CAMERA + SLIDE LOADING ───────────────
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Load slide filenames sorted naturally (1.png before 10.png)
    pathImages = sorted(os.listdir(PRESENTATION_FOLDER), key=len)
    if not pathImages:
        print("[ERROR] No images found in 'Presentation' folder.")
        print("        Please add PNG slides (1.png, 2.png, ...) and restart.")
        return

    print(f"[INFO] Loaded {len(pathImages)} slides from 'Presentation' folder")
    for i, name in enumerate(pathImages):
        print(f"       Slide {i}: {name}")

    # Current slide index
    imgNumber = 0

    # ──────────────────────── STEP 2: HAND DETECTOR ────────────────────────
    detector = HandDetector(detectionCon=0.8, maxHands=1)

    # ──────────────────────── STEP 3: STATE VARIABLES ──────────────────────

    # Button debounce
    buttonPressed  = False
    buttonCounter  = 0

    # Drawing / annotation state
    annotations      = [[]]   # List of strokes (each stroke is a list of points)
    annotationNumber = 0
    annotationStart  = False

    print("\n--- Presentation Controller Running ---")
    print("    Raise hand above the green line to navigate.")
    print("    Press 'q' to quit.\n")

    # ──────────────────────── MAIN LOOP ─────────────────────────────────────
    while True:
        success, img = cap.read()
        if not success:
            continue

        # Mirror the webcam (more intuitive)
        img = cv2.flip(img, 1)

        # Load the current slide
        slidePath = os.path.join(PRESENTATION_FOLDER, pathImages[imgNumber])
        imgCurrent = cv2.imread(slidePath)
        if imgCurrent is None:
            print(f"[WARN] Could not read slide: {slidePath}")
            continue

        # Get the slide dimensions (may differ from camera)
        h_slide, w_slide, _ = imgCurrent.shape

        # Detect hands
        hands, img = detector.findHands(img, flipType=False)

        # ──────────── GESTURE THRESHOLD LINE (visual feedback) ─────────────
        cv2.line(img, (0, gestureThreshold), (width, gestureThreshold),
                 (0, 255, 0), 2)

        # ──────────── BUTTON DEBOUNCE LOGIC ────────────────────────────────
        if buttonPressed:
            buttonCounter += 1
            if buttonCounter > buttonDelay:
                buttonPressed = False
                buttonCounter = 0

        # ──────────── PROCESS HAND GESTURES ────────────────────────────────
        if hands and not buttonPressed:
            hand = hands[0]
            cx, cy = hand["center"]       # Center of the palm
            lmList = hand["lmList"]        # 21 landmarks
            fingers = detector.fingersUp(hand)  # e.g. [1,0,0,0,0]

            # ── STEP 5: Interpolate index finger to slide coordinates ──────
            # Map a centered sub-region of the camera to the full slide
            xVal = int(np.interp(lmList[8][0], [width // 2, width], [0, w_slide]))
            yVal = int(np.interp(lmList[8][1], [150, height - 150], [0, h_slide]))
            indexFinger = (xVal, yVal)

            # ── STEP 4: SLIDE NAVIGATION (only above threshold) ────────────
            if cy <= gestureThreshold:

                # PREVIOUS SLIDE — thumb only
                if fingers == [1, 0, 0, 0, 0] and imgNumber > 0:
                    imgNumber -= 1
                    buttonPressed = True
                    annotations = [[]]
                    annotationNumber = 0
                    annotationStart = False
                    print(f"  ◀ Slide {imgNumber}")

                # NEXT SLIDE — pinky only
                if fingers == [0, 0, 0, 0, 1] and imgNumber < len(pathImages) - 1:
                    imgNumber += 1
                    buttonPressed = True
                    annotations = [[]]
                    annotationNumber = 0
                    annotationStart = False
                    print(f"  ▶ Slide {imgNumber}")

            # ── STEP 6A: LASER POINTER — index + middle fingers ────────────
            if fingers == [0, 1, 1, 0, 0]:
                cv2.circle(imgCurrent, indexFinger, POINTER_RADIUS,
                           POINTER_COLOR, cv2.FILLED)
                annotationStart = False   # Stop drawing stroke

            # ── STEP 6B: DRAW — index finger only ─────────────────────────
            elif fingers == [0, 1, 0, 0, 0]:
                if not annotationStart:
                    annotationStart = True
                    annotationNumber += 1
                    annotations.append([])
                cv2.circle(imgCurrent, indexFinger, POINTER_RADIUS,
                           POINTER_COLOR, cv2.FILLED)
                annotations[annotationNumber].append(indexFinger)

            # ── STEP 6C: ERASE LAST STROKE — index + middle + ring ────────
            elif fingers == [0, 1, 1, 1, 0]:
                if annotations and annotationNumber >= 0:
                    annotations.pop(-1)
                    annotationNumber -= 1
                    buttonPressed = True
                annotationStart = False

            else:
                annotationStart = False

        # ──────────── STEP 7: RENDER ALL ANNOTATIONS ON SLIDE ──────────────
        for stroke in annotations:
            for j in range(1, len(stroke)):
                cv2.line(imgCurrent, stroke[j - 1], stroke[j],
                         DRAW_COLOR, DRAW_THICKNESS)

        # ──────────── STEP 2 (cont): PiP OVERLAY ──────────────────────────
        imgSmall = cv2.resize(img, (PIP_WIDTH, PIP_HEIGHT))
        imgCurrent[0:PIP_HEIGHT, w_slide - PIP_WIDTH:w_slide] = imgSmall

        # ──────────── SLIDE NUMBER INDICATOR ───────────────────────────────
        slideText = f"Slide {imgNumber + 1}/{len(pathImages)}"
        cv2.putText(imgCurrent, slideText, (10, h_slide - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # ──────────── SHOW WINDOWS ─────────────────────────────────────────
        cv2.imshow("Image", img)
        cv2.imshow("Slides", imgCurrent)

        # Quit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("--- Presentation Controller Stopped ---")


if __name__ == "__main__":
    main()
