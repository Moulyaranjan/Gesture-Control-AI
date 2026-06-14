import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from pynput.mouse import Controller, Button
import math

import mss
import time
import os


# ==========================
# Mouse Controller
# ==========================

mouse = Controller()

left_clicked = False
right_clicked = False

last_shot = 0

os.makedirs("screenshots", exist_ok=True)

prev_x = 0
prev_y = 0

SMOOTHING = 7

# ==========================
# Hand Model
# ==========================

base_options = python.BaseOptions(
    model_asset_path="models/hand_landmarker.task"
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
)

detector = vision.HandLandmarker.create_from_options(options)

# ==========================
# Webcam
# ==========================

cap = cv2.VideoCapture(0)

# Change according to your screen
import tkinter as tk

root = tk.Tk()

SCREEN_W = root.winfo_screenwidth()
SCREEN_H = root.winfo_screenheight()

root.destroy()

# Hand Skeleton Connections

connections = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    result = detector.detect(mp_image)

    h, w, _ = frame.shape

    if result.hand_landmarks:

        for hand in result.hand_landmarks:

            points = {}

            # ==========================
            # Landmarks
            # ==========================

            for idx, landmark in enumerate(hand):

                x = int(landmark.x * w)
                y = int(landmark.y * h)

                points[idx] = (x, y)

                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0, 255, 0),
                    -1
                )

                cv2.putText(
                    frame,
                    str(idx),
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 0, 0),
                    1
                )

                # ==========================
                # Virtual Mouse
                # ==========================

                if idx == 8:

                    screen_x = int(landmark.x * SCREEN_W)
                    screen_y = int(landmark.y * SCREEN_H)

                    curr_x = prev_x + (screen_x - prev_x) / SMOOTHING
                    curr_y = prev_y + (screen_y - prev_y) / SMOOTHING

                    mouse.position = (int(curr_x), int(curr_y))

                    prev_x = curr_x
                    prev_y = curr_y

            # ==========================
            # Draw Skeleton
            # ==========================

            for start, end in connections:

                if start in points and end in points:

                    cv2.line(
                        frame,
                        points[start],
                        points[end],
                        (0, 255, 0),
                        2
                    )

            # ==========================
            # Left Click
            # Thumb Tip = 4
            # Index Tip = 8
            # ==========================

            if 4 in points and 8 in points:

                x1, y1 = points[4]
                x2, y2 = points[8]

                left_distance = math.sqrt(
                    (x2 - x1) ** 2 +
                    (y2 - y1) ** 2
                )

                cv2.line(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 0, 0),
                    2
                )

                if left_distance < 30 and not left_clicked:

                    mouse.click(Button.left, 1)

                    left_clicked = True

                    cv2.putText(
                        frame,
                        "LEFT CLICK",
                        (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )

                elif left_distance > 40:

                    left_clicked = False

            # ==========================
            # Right Click
            # Thumb Tip = 4
            # Middle Tip = 12
            # ==========================

            if 4 in points and 12 in points:

                x1, y1 = points[4]
                x2, y2 = points[12]

                right_distance = math.sqrt(
                    (x2 - x1) ** 2 +
                    (y2 - y1) ** 2
                )

                if right_distance < 30 and not right_clicked:

                    mouse.click(Button.right, 1)

                    right_clicked = True

                    cv2.putText(
                        frame,
                        "RIGHT CLICK",
                        (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 0, 255),
                        2
                    )

                elif right_distance > 40:

                    right_clicked = False

                    # ==========================
                    # Scroll Gesture
                    # ==========================

                if 8 in points:

                 index_y = points[8][1]
         
                 if index_y < 100:
                   mouse.scroll(0, 2)

                 cv2.putText(
                 frame,
                 "SCROLL UP",
                  (20, 150),
                  cv2.FONT_HERSHEY_SIMPLEX,
                  1,
                  (255, 255, 0),
                  2
                 )

                elif index_y > 350:
                 mouse.scroll(0, -2)

                 cv2.putText(
                 frame,
                 "SCROLL DOWN",
                 (20, 150),
                  cv2.FONT_HERSHEY_SIMPLEX,
                  1,
                 (255, 255, 0),
                  2
                 )
        
          # ==========================
          # Screenshot Gesture
          # Thumb Tip = 4
          # Pinky Tip = 20
          # ==========================
           # Screenshot Gesture
        if 4 in points and 20 in points:

         x1, y1 = points[4]
         x2, y2 = points[20]

         distance = math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
       )

        if distance < 30:

         current_time = time.time()

         if current_time - last_shot > 3:

            filepath = (
                "screenshots/"
                f"shot_{int(current_time)}.png"
            )

            with mss.mss() as sct:
                sct.shot(output=filepath)

            print("Saved:", filepath)

            last_shot = current_time

            cv2.putText(
                frame,
                "SCREENSHOT SAVED",
                (20, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )

    cv2.imshow("Gesture Control AI", frame)

    if cv2.waitKey(1) & 0xFF == 27:
      break

cap.release()
cv2.destroyAllWindows()