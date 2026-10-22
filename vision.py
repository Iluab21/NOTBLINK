import cv2
import time
import math
import numpy as np
import mediapipe as mp


LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]

HEAD_POINTS = [10, 1, 152]


def euclidean_dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def calculate_ear(landmarks, eye_indices, frame_w, frame_h):
    """Calculates Eye Aspect Ratio (EAR) for a given eye."""
    pts = [(int(landmarks[idx].x * frame_w), int(landmarks[idx].y * frame_h)) for idx in eye_indices]

    p1, p2, p3, p4, p5, p6 = pts
    dist_v1 = euclidean_dist(p2, p6)
    dist_v2 = euclidean_dist(p3, p5)
    dist_h = euclidean_dist(p1, p4)

    if dist_h == 0:
        return 0.0
    return (dist_v1 + dist_v2) / (2.0 * dist_h)


def is_head_pitched_down(landmarks, frame_w, frame_h) -> bool:
    """Detects if head is tilted downwards towards keyboard/desk."""
    forehead = landmarks[10]
    nose = landmarks[1]
    chin = landmarks[152]

    upper_face = abs(nose.y - forehead.y)
    lower_face = abs(chin.y - nose.y)

    if lower_face == 0:
        return False

    ratio = upper_face / lower_face
    return ratio < 0.65


class BlinkDetector:
    def __init__(self, config: dict):
        self.camera_idx = config["camera"].get("camera_index", 0)
        self.width = config["camera"].get("width", 640)
        self.height = config["camera"].get("height", 480)
        self.base_threshold = config["camera"].get("ear_threshold", 0.20)
        self.consecutive_frames = config["camera"].get("consecutive_closed_frames", 1)
        self.cooldown_sec = config["camera"].get("cooldown_seconds", 0.45)
        self.pitch_check = config["camera"].get("keyboard_look_down_protection", True)

        self.show_eye_contours = config["camera"].get("show_eye_contours", False)
        self.show_action_banner = config["camera"].get("show_action_banner", False)
        self.show_hud = config["camera"].get("show_hud", True)

        self.closed_frame_count = 0
        self.last_blink_time = 0.0

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.cap = None

    def start_camera(self) -> bool:
        try:
            self.cap = cv2.VideoCapture(self.camera_idx, cv2.CAP_DSHOW)
        except Exception:
            self.cap = None

        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_idx)

        if not self.cap.isOpened():
            print(f"[Vision] Could not open camera {self.camera_idx}!")
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return True

    def process_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return False, None, False, 0.0, False

        ret, frame = self.cap.read()
        if not ret:
            return False, None, False, 0.0, False

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        blink_detected = False
        avg_ear = 0.0
        head_down = False

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            left_ear = calculate_ear(landmarks, LEFT_EYE_POINTS, w, h)
            right_ear = calculate_ear(landmarks, RIGHT_EYE_POINTS, w, h)
            avg_ear = (left_ear + right_ear) / 2.0

            if self.pitch_check:
                head_down = is_head_pitched_down(landmarks, w, h)

            effective_threshold = self.base_threshold - 0.04 if head_down else self.base_threshold

            now = time.time()
            if avg_ear < effective_threshold:
                self.closed_frame_count += 1
                if self.closed_frame_count >= self.consecutive_frames:
                    if (now - self.last_blink_time) > self.cooldown_sec:
                        blink_detected = True
                        self.last_blink_time = now
            else:
                self.closed_frame_count = 0

            if self.show_eye_contours:
                self._draw_eye_contours(frame, landmarks, w, h)

        return True, frame, blink_detected, avg_ear, head_down

    def _draw_eye_contours(self, frame, landmarks, w, h):
        for points in [LEFT_EYE_POINTS, RIGHT_EYE_POINTS]:
            pts = np.array([(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in points], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (0, 255, 255), 1)

    def draw_hud(self, frame, blink_count: int, boss_interval: int, last_action: str, avg_ear: float, head_down: bool, is_paused: bool = False):
        h, w, _ = frame.shape
        if not self.show_hud:
            if is_paused:
                cv2.rectangle(frame, (w - 140, 15), (w - 15, 45), (0, 140, 255), -1)
                cv2.putText(frame, "PAUSED", (w - 125, 37),
                            cv2.FONT_HERSHEY_DUPLEX, 0.6, (15, 15, 25), 2)
            return

        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (w - 10, 90), (15, 15, 25), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)


        border_color = (0, 165, 255) if is_paused else (0, 220, 255)
        cv2.rectangle(frame, (10, 10), (w - 10, 90), border_color, 2 if is_paused else 1)


        cv2.putText(frame, f"BLINKS: {blink_count}", (25, 45),
                    cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2)



        if is_paused:
            cv2.rectangle(frame, (w - 180, 18), (w - 20, 50), (0, 140, 255), -1)
            cv2.putText(frame, "|| PAUSED", (w - 165, 42),
                        cv2.FONT_HERSHEY_DUPLEX, 0.65, (15, 15, 25), 2)


        ear_text = f"EAR: {avg_ear:.2f} (Thresh: {self.base_threshold:.2f})"
        cv2.putText(frame, ear_text, (25, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        pitch_text = "HEAD: DOWN" if head_down else "HEAD: OK"
        pitch_color = (0, 165, 255) if head_down else (0, 255, 0)
        cv2.putText(frame, pitch_text, (330, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, pitch_color, 1)

        if self.show_action_banner and last_action:
            cv2.rectangle(frame, (10, h - 50), (w - 10, h - 10), (10, 10, 40), -1)
            cv2.rectangle(frame, (10, h - 50), (w - 10, h - 10), (0, 100, 255), 1)
            cv2.putText(frame, f">> {last_action}", (25, h - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

    def release(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
