import threading
import time

import cv2
import mediapipe as mp
import serial

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
MODEL_PATH = "hand_landmarker.task"
CAMERA_INDEX = 0
MAX_HANDS = 2
WINDOW_TITLE = "Hand Tracker"

# Change this to your arduino port
PORT = "COM7"
INTERVAL = 30 # ms

FINGERTIP_IDS = [8, 12, 16, 20]  # index → pinky tips
KNUCKLE_OFFSET = 2  # tip_id - 2 = middle knuckle

# Colours (BGR)
COL_GREEN = (0, 220, 80)
COL_BLUE = (255, 120, 0)
COL_WHITE = (255, 255, 255)
COL_BLACK = (0, 0, 0)
COL_JOINT = (180, 230, 255)
COL_BONE = (100, 180, 255)

# Landmark connectivity for drawing the hand skeleton
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),  # index
    (5, 9), (9, 10), (10, 11), (11, 12),  # middle
    (9, 13), (13, 14), (14, 15), (15, 16),  # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),  # palm base
]

# ──────────────────────────────────────────────
# Finger counter
# ──────────────────────────────────────────────
def count_fingers(landmarks: list, hand_label: str) -> int:
    """
    Count raised fingers for one hand.

    MediaPipe labels hands from the *camera's* perspective, but because we
    mirror the frame (cv2.flip) the labels are already correct for the user:
      - "Right" label  →  user's right hand  →  thumb tip is to the LEFT of
                          the thumb base when the hand is open.
      - "Left"  label  →  user's left hand   →  thumb tip is to the RIGHT.
    """
    count = 0

    # Thumb: compare x-positions of tip (4) and IP joint (3).
    # Because we mirror the frame before detection, MediaPipe's labels are
    # flipped relative to the user: "Right" → user's left hand, "Left" → user's right.
    # After the mirror, a user's LEFT hand has its thumb on the RIGHT (larger x),
    # and a user's RIGHT hand has its thumb on the LEFT (smaller x).
    if hand_label == "Right":  # actually user's left hand post-flip
        if landmarks[4].x > landmarks[3].x:
            count += 1
    else:  # actually user's right hand post-flip
        if landmarks[4].x < landmarks[3].x:
            count += 1

    # Index → Pinky: tip above its middle knuckle (lower y = higher on screen)
    for tip_id in FINGERTIP_IDS:
        if landmarks[tip_id].y < landmarks[tip_id - KNUCKLE_OFFSET].y:
            count += 1

    return count


# ──────────────────────────────────────────────
# Drawing helpers
# ──────────────────────────────────────────────
def draw_landmarks(frame: cv2.Mat, landmarks: list) -> None:
    h, w = frame.shape[:2]

    # Connections first (drawn under the joints)
    for a, b in HAND_CONNECTIONS:
        ax = int(landmarks[a].x * w)
        ay = int(landmarks[a].y * h)
        bx = int(landmarks[b].x * w)
        by = int(landmarks[b].y * h)
        cv2.line(frame, (ax, ay), (bx, by), COL_BONE, 2, cv2.LINE_AA)

    # Joint dots
    for lm in landmarks:
        cx = int(lm.x * w)
        cy = int(lm.y * h)
        cv2.circle(frame, (cx, cy), 5, COL_JOINT, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 5, COL_WHITE, 1, cv2.LINE_AA)


def draw_label(frame: cv2.Mat, text: str, pos: tuple[int, int],
               color: tuple = COL_GREEN, scale: float = 0.9) -> None:
    """Draw text with a dark drop-shadow for readability."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    ox, oy = pos
    cv2.putText(frame, text, (ox + 1, oy + 1), font, scale, COL_BLACK, thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (ox, oy), font, scale, color, thickness, cv2.LINE_AA)


# ──────────────────────────────────────────────
# Hand tracker class
# ──────────────────────────────────────────────
class HandTracker:
    def __init__(self, model_path: str = MODEL_PATH,
                 num_hands: int = MAX_HANDS,
                 camera_index: int = CAMERA_INDEX, on_numbers_detected=None) -> None:

        self.on_numbers_detected = on_numbers_detected

        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOpts = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOpts(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=num_hands,
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.cap = cv2.VideoCapture(camera_index)
        self._fps_time = time.monotonic()
        self._fps = 0.0

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {camera_index}")

    # ── core loop ──────────────────────────────
    def run(self) -> None:
        try:
            # Make window resizable
            cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)

            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                result = self._detect(frame)
                frame = self._render(frame, result)

                cv2.imshow(WINDOW_TITLE, frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
        finally:
            self.release()

    # ── detection ──────────────────────────────
    def _detect(self, frame: cv2.Mat):
        # Use the camera's own clock for accurate VIDEO-mode timestamps
        timestamp_ms = int(self.cap.get(cv2.CAP_PROP_POS_MSEC))

        # Fallback: camera may report 0 ms on some backends
        if timestamp_ms == 0:
            timestamp_ms = int(time.monotonic() * 1000)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    # ── rendering ──────────────────────────────
    def _render(self, frame: cv2.Mat, result) -> cv2.Mat:
        self._update_fps()

        left_count = 0
        right_count = 0

        if result.hand_landmarks:
            for i, landmarks in enumerate(result.hand_landmarks):
                label = (result.handedness[i][0].category_name
                         if result.handedness else "Right")

                fingers = count_fingers(landmarks, label)

                # Assign correctly
                if label == "Left":
                    left_count = fingers
                else:
                    right_count = fingers

                draw_landmarks(frame, landmarks)
                draw_label(frame, f"{label}: {fingers}",
                           (30, 90 + i * 45), COL_GREEN)

            total = left_count + right_count
            draw_label(frame, f"Total: {total}", (30, 45), COL_BLUE, scale=1.0)

        # Call the callback
        if self.on_numbers_detected:
            self.on_numbers_detected(left_count, right_count)

        draw_label(frame, f"FPS: {self._fps:.1f}",
                   (frame.shape[1] - 140, 35), COL_WHITE, scale=0.75)

        return frame
    # ── FPS ────────────────────────────────────
    def _update_fps(self) -> None:
        now = time.monotonic()
        delta = now - self._fps_time
        self._fps = 1.0 / delta if delta > 0 else 0.0
        self._fps_time = now

    # ── cleanup ────────────────────────────────
    def release(self) -> None:
        self.cap.release()
        self.landmarker.close()
        cv2.destroyAllWindows()


class ArduinoSender:
    def __init__(self, port=PORT, baudrate=9600, interval = INTERVAL):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self._left = 0
        self._right = 0
        self._last = None
        self.running = True
        self.interval = interval

        self.t = threading.Thread(target=self._worker, daemon=True)
        self.t.start()

    def send(self, left, right):
        self._left = left
        self._right = right

    def _worker(self):
        while self.running:
            time.sleep(0.001 * self.interval)  # 30 ms interval

            val = (self._left, self._right)
            if val == self._last:
                continue

            print("left, right = ", self._left, self._right)
            self.ser.write(f"{self._left},{self._right}\n".encode())
            self._last = val

    def close(self):
        self.running = False
        self.ser.close()
# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    arduino = ArduinoSender(port=PORT, baudrate=9600)


    def handle_numbers(left, right):
        arduino.send(left, right)

    tracker = HandTracker(on_numbers_detected=handle_numbers)
    tracker.run()
