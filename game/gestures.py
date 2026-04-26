from __future__ import annotations

import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Mapping, Sequence

try:
    import joblib as _joblib
except ModuleNotFoundError:
    _joblib = None  # type: ignore[assignment]

# ML gesture classifier label map
# 0 = INDEX_SWORD  1 = FIST  2 = OPEN_PALM  3 = SPEED_UP  4 = SKILL
_GESTURE_LABEL_MAP: dict[int, str] = {
    0: "INDEX_SWORD",
    1: "FIST",
    2: "OPEN_PALM",
    3: "SPEED_UP",
    4: "SKILL",
}

from .config import CAMERA_GAME_BOTTOM, CAMERA_GAME_LEFT, CAMERA_GAME_RIGHT, CAMERA_GAME_TOP


INDEX_TIP = 8
INDEX_PIP = 6
MIDDLE_TIP = 12
MIDDLE_PIP = 10
RING_TIP = 16
RING_PIP = 14
PINKY_TIP = 20
PINKY_PIP = 18
THUMB_TIP = 4
THUMB_IP = 3
WRIST = 0
INDEX_MCP = 5
MIDDLE_MCP = 9
RING_MCP = 13
PINKY_MCP = 17


@dataclass(frozen=True)
class LandmarkPoint:
    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class GestureState:
    mode: str = "NONE"
    fingertip: tuple[int, int] | None = None
    palm_center: tuple[int, int] | None = None
    camera_fingertip: tuple[float, float] | None = None
    camera_palm_center: tuple[float, float] | None = None
    tracking_points: tuple[tuple[float, float], ...] = ()
    visible_fingers: int = 0
    confidence: float = 0.0
    source: str = "camera"


HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (5, 9),
    (9, 13),
    (13, 17),
)


def classify_fingers(landmarks: Sequence[LandmarkPoint]) -> Mapping[str, bool]:
    if len(landmarks) < 21:
        return {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}

    margin = 0.025
    wrist = landmarks[WRIST]
    thumb_tip = landmarks[THUMB_TIP]
    thumb_ip = landmarks[THUMB_IP]
    hand_width = abs(landmarks[INDEX_MCP].x - landmarks[PINKY_MCP].x)
    thumb_margin = max(0.025, hand_width * 0.12)

    return {
        "thumb": abs(thumb_tip.x - wrist.x) > abs(thumb_ip.x - wrist.x) + thumb_margin,
        "index": landmarks[INDEX_TIP].y < landmarks[INDEX_PIP].y - margin,
        "middle": landmarks[MIDDLE_TIP].y < landmarks[MIDDLE_PIP].y - margin,
        "ring": landmarks[RING_TIP].y < landmarks[RING_PIP].y - margin,
        "pinky": landmarks[PINKY_TIP].y < landmarks[PINKY_PIP].y - margin,
    }


def classify_pose(landmarks: Sequence[LandmarkPoint]) -> tuple[str, int]:
    fingers = classify_fingers(landmarks)
    visible_count = sum(1 for is_visible in fingers.values() if is_visible)
    four_main_fingers = fingers["index"] and fingers["middle"] and fingers["ring"] and fingers["pinky"]

    if visible_count >= 4 or four_main_fingers:
        return "OPEN_PALM", visible_count

    if visible_count == 0:
        return "FIST", visible_count

    if fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
        return "INDEX_SWORD", visible_count

    return "NONE", visible_count


def map_camera_to_screen(x: float, y: float, screen_size: tuple[int, int]) -> tuple[int, int]:
    width, height = screen_size
    mapped_x = (x - CAMERA_GAME_LEFT) / (CAMERA_GAME_RIGHT - CAMERA_GAME_LEFT)
    mapped_y = (y - CAMERA_GAME_TOP) / (CAMERA_GAME_BOTTOM - CAMERA_GAME_TOP)
    mapped_x = max(0.0, min(1.0, mapped_x))
    mapped_y = max(0.0, min(1.0, mapped_y))
    return int(mapped_x * width), int(mapped_y * height)


class HandTracker:
    def __init__(self, max_num_hands: int = 1) -> None:
        self.available = False
        self.error: str | None = None
        self._mp = None
        self._hands = None
        self._backend = "none"
        self._cv2 = None
        self._np = None

        # ML gesture classifier (optional — gracefully absent)
        self.clf = None
        if _joblib is not None:
            model_path = Path("assets/models/gesture_classifier.pkl")
            if model_path.exists():
                try:
                    self.clf = _joblib.load(model_path)
                    print(f"[gestures] ML classifier loaded from {model_path}")
                except Exception as exc:
                    print(f"[gestures] Could not load classifier: {exc}")

        try:
            import mediapipe as mp
        except ModuleNotFoundError as exc:
            self._enable_color_tracker(f"MediaPipe unavailable: {exc}")
            return

        self._mp = mp
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            self._hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=max_num_hands,
                model_complexity=1,
                min_detection_confidence=0.58,
                min_tracking_confidence=0.55,
            )
            self._backend = "solutions"
            self.available = True
            return

        if hasattr(mp, "tasks") and hasattr(mp.tasks, "vision"):
            model_path = self._find_tasks_model()
            if model_path is None:
                self._enable_color_tracker("MediaPipe Tasks model missing")
                return
            try:
                # Use model_asset_buffer instead of model_asset_path so that
                # MediaPipe's C++ layer never sees the file path — this is the
                # only fix needed for Windows usernames with non-ASCII characters.
                base_options = mp.tasks.BaseOptions(
                    model_asset_buffer=model_path.read_bytes(),
                    delegate=mp.tasks.BaseOptions.Delegate.CPU,
                )
                options = mp.tasks.vision.HandLandmarkerOptions(
                    base_options=base_options,
                    running_mode=mp.tasks.vision.RunningMode.VIDEO,
                    num_hands=max_num_hands,
                    min_hand_detection_confidence=0.58,
                    min_hand_presence_confidence=0.55,
                    min_tracking_confidence=0.55,
                )
                self._hands = mp.tasks.vision.HandLandmarker.create_from_options(options)
            except Exception as exc:
                self._enable_color_tracker(f"MediaPipe Tasks failed: {exc}")
                return
            self._backend = "tasks"
            self.available = True
            return

        self._enable_color_tracker("installed MediaPipe package has no Hands or HandLandmarker API")

    # ------------------------------------------------------------------
    # ML inference
    # ------------------------------------------------------------------

    def _predict_gesture(self, landmarks: list[LandmarkPoint]) -> tuple[str, int]:
        """Run the trained sklearn classifier and return (mode, visible_fingers).

        Pre-processing mirrors the training / test scripts:
          1. Subtract wrist (landmark 0) so the hand is origin-centred.
          2. Normalise by the maximum absolute value so scale is invariant.
        Falls back to rule-based classify_pose when the model is absent or
        raises an exception.
        """
        if self.clf is None:
            return classify_pose(landmarks)

        wrist = landmarks[0]
        raw: list[float] = []
        for lm in landmarks:
            raw.extend([lm.x - wrist.x, lm.y - wrist.y])

        max_val = max(abs(v) for v in raw) if raw else 1.0
        if max_val == 0.0:
            max_val = 1.0
        features = [v / max_val for v in raw]

        try:
            pred_idx = int(self.clf.predict([features])[0])
        except Exception:
            return classify_pose(landmarks)

        mode = _GESTURE_LABEL_MAP.get(pred_idx, "NONE")
        # Reuse rule-based finger count for HUD / calibration meter
        visible = sum(1 for up in classify_fingers(landmarks).values() if up)
        return mode, visible

    # ------------------------------------------------------------------

    def _enable_color_tracker(self, reason: str) -> None:
        try:
            import cv2
            import numpy as np
        except ModuleNotFoundError as exc:
            self.error = f"{reason}; OpenCV fallback unavailable: {exc}"
            return

        self._cv2 = cv2
        self._np = np
        self._backend = "color"
        self.available = True
        self.error = "MediaPipe hand tracker unavailable; using OpenCV color hand tracker"

    def _find_tasks_model(self) -> Path | None:
        configured_path = os.environ.get("HAND_LANDMARKER_MODEL")
        candidates = []
        if configured_path:
            candidates.append(Path(configured_path))
        candidates.append(Path(__file__).resolve().parent.parent / "assets" / "models" / "hand_landmarker.task")

        for path in candidates:
            if path.exists():
                return path
        return None

    def process(self, rgb_frame, screen_size: tuple[int, int]) -> GestureState:
        if not self.available:
            return GestureState(source="unavailable")
        if self._backend != "color" and self._hands is None:
            return GestureState(source="unavailable")

        if self._backend == "solutions":
            results = self._hands.process(rgb_frame)
            raw_landmarks = results.multi_hand_landmarks[0].landmark if results.multi_hand_landmarks else None
        elif self._backend == "tasks":
            image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb_frame)
            ts_ms = int(time.monotonic() * 1000)
            if hasattr(self, '_last_ts_ms') and ts_ms <= self._last_ts_ms:
                ts_ms = self._last_ts_ms + 1
            self._last_ts_ms = ts_ms
            results = self._hands.detect_for_video(image, ts_ms)
            raw_landmarks = results.hand_landmarks[0] if results.hand_landmarks else None
        elif self._backend == "color":
            return self._process_color(rgb_frame, screen_size)
        else:
            raw_landmarks = None

        if not raw_landmarks:
            return GestureState(confidence=0.0)

        landmarks = [LandmarkPoint(point.x, point.y, point.z) for point in raw_landmarks]
        mode, visible_count = self._predict_gesture(landmarks)
        fingertip = landmarks[INDEX_TIP]
        palm_points = [landmarks[index] for index in (WRIST, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP)]
        palm_x = sum(point.x for point in palm_points) / len(palm_points)
        palm_y = sum(point.y for point in palm_points) / len(palm_points)

        return GestureState(
            mode=mode,
            fingertip=map_camera_to_screen(fingertip.x, fingertip.y, screen_size),
            palm_center=map_camera_to_screen(palm_x, palm_y, screen_size),
            camera_fingertip=(fingertip.x, fingertip.y),
            camera_palm_center=(palm_x, palm_y),
            tracking_points=tuple((point.x, point.y) for point in landmarks),
            visible_fingers=visible_count,
            confidence=1.0,
        )

    def _process_color(self, rgb_frame, screen_size: tuple[int, int]) -> GestureState:
        if self._cv2 is None or self._np is None:
            return GestureState(source="unavailable")

        cv2 = self._cv2
        np = self._np
        hsv = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2HSV)
        lower_skin = np.array([0, 32, 45], dtype=np.uint8)
        upper_skin = np.array([28, 190, 255], dtype=np.uint8)
        lower_skin_red = np.array([160, 32, 45], dtype=np.uint8)
        upper_skin_red = np.array([179, 190, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower_skin_red, upper_skin_red))

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return GestureState(confidence=0.0, source="color-camera")

        contour = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(contour))
        if area < 2500:
            return GestureState(confidence=0.0, source="color-camera")

        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            return GestureState(confidence=0.0, source="color-camera")

        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        points = contour.reshape(-1, 2)
        distances = ((points[:, 0] - cx) ** 2 + (points[:, 1] - cy) ** 2)
        fingertip_raw = points[int(distances.argmax())]
        
        x, y, w, h = cv2.boundingRect(contour)

        visible_fingers = self._estimate_fingers(cv2, contour)
        box_area = max(1, w * h)
        area_ratio = area / box_area
        open_palm = visible_fingers >= 4 or (area > 15000 and w > 105 and h > 105 and area_ratio > 0.42)
        compact_fist = visible_fingers <= 1 and area > 9000 and area_ratio > 0.52 and w > 78 and h > 78
        mode = "OPEN_PALM" if open_palm else "FIST" if compact_fist else "INDEX_SWORD"

        camera_tip = (float(fingertip_raw[0]) / rgb_frame.shape[1], float(fingertip_raw[1]) / rgb_frame.shape[0])
        camera_palm = (float(cx) / rgb_frame.shape[1], float(cy) / rgb_frame.shape[0])
        fingertip = map_camera_to_screen(camera_tip[0], camera_tip[1], screen_size)
        palm_center = map_camera_to_screen(camera_palm[0], camera_palm[1], screen_size)
        confidence = max(0.0, min(1.0, area / 42000.0))
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True).reshape(-1, 2)
        if len(approx) > 64:
            sample_step = max(1, len(approx) // 64)
            approx = approx[::sample_step]
        tracking_points = tuple((float(point[0]) / rgb_frame.shape[1], float(point[1]) / rgb_frame.shape[0]) for point in approx)
        return GestureState(
            mode=mode,
            fingertip=fingertip,
            palm_center=palm_center,
            camera_fingertip=camera_tip,
            camera_palm_center=camera_palm,
            tracking_points=tracking_points,
            visible_fingers=max(1, visible_fingers),
            confidence=confidence,
            source="color-camera",
        )

    def _estimate_fingers(self, cv2, contour) -> int:
        if len(contour) < 5:
            return 1

        hull = cv2.convexHull(contour, returnPoints=False)
        if hull is None or len(hull) < 4:
            return 1

        defects = cv2.convexityDefects(contour, hull)
        if defects is None:
            return 1

        count = 1
        for defect in defects[:, 0]:
            start_index, end_index, far_index, depth = defect
            start = contour[start_index][0]
            end = contour[end_index][0]
            far = contour[far_index][0]
            a = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
            b = ((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2) ** 0.5
            c = ((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2) ** 0.5
            if b == 0 or c == 0:
                continue
            angle = (b * b + c * c - a * a) / (2 * b * c)
            angle = max(-1.0, min(1.0, angle))
            if depth > 6500 and angle > 0.15:
                count += 1
        return min(5, count)

    def close(self) -> None:
        if self._hands is not None:
            self._hands.close()
