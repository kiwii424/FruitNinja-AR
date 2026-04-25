from __future__ import annotations

import json
import os
import platform
import subprocess


CAMERA_INDEX_ENV = "ARFN_CAMERA_INDEX"
ALLOW_IPHONE_CAMERA_ENV = "ARFN_CAMERA_ALLOW_IPHONE"
IPHONE_CAMERA_MARKERS = ("iphone", "ipad", "continuity")
VIRTUAL_CAMERA_MARKERS = ("obs", "virtual", "camo", "epoccam", "droidcam", "ndi", "snap camera")
BUILTIN_CAMERA_MARKERS = ("facetime", "built-in", "builtin", "macbook", "imac", "display camera")


def parse_system_profiler_camera_names(output: str) -> list[str]:
    if not output.strip():
        return []

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return _parse_plaintext_camera_names(output)

    names: list[str] = []

    def collect(value) -> None:
        if isinstance(value, dict):
            name = value.get("_name")
            if isinstance(name, str) and name.strip() and name.strip().lower() != "camera":
                names.append(name.strip())
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(data.get("SPCameraDataType", data))
    return _unique(names)


def _parse_plaintext_camera_names(output: str) -> list[str]:
    names: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.endswith(":"):
            continue
        name = line[:-1].strip()
        if not name or name.lower() in {"camera", "cameras"}:
            continue
        names.append(name)
    return _unique(names)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def mac_camera_device_names() -> list[str]:
    if platform.system() != "Darwin":
        return []
    try:
        result = subprocess.run(
            ["system_profiler", "-json", "SPCameraDataType"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return parse_system_profiler_camera_names(result.stdout)


def camera_index_order(
    preferred_index: int,
    device_names: list[str] | None = None,
    *,
    max_probe: int = 4,
    allow_iphone: bool = False,
) -> list[int]:
    device_names = device_names or []
    if not device_names:
        if preferred_index == 0 and platform.system() == "Darwin":
            return [1, 0, *[index for index in range(2, max_probe)]]
        return [preferred_index, *[index for index in range(max_probe) if index != preferred_index]]

    ranked: list[tuple[int, int]] = []
    highest_known_index = max(len(device_names), max_probe)
    for index in range(highest_known_index):
        name = device_names[index] if index < len(device_names) else ""
        if name and _is_rejected_camera_name(name) and not allow_iphone:
            continue

        score = 0
        if index == preferred_index:
            score += 10
        if name:
            score += 5
        if _is_builtin_camera_name(name):
            score += 100
        if _is_virtual_camera_name(name):
            score -= 40
        if _is_iphone_camera_name(name):
            score -= 80
        ranked.append((score, index))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [index for _, index in ranked]


def env_camera_index() -> int | None:
    value = os.environ.get(CAMERA_INDEX_ENV)
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _is_iphone_camera_name(name: str) -> bool:
    lowered = name.casefold()
    return any(marker in lowered for marker in IPHONE_CAMERA_MARKERS)


def _is_virtual_camera_name(name: str) -> bool:
    lowered = name.casefold()
    return any(marker in lowered for marker in VIRTUAL_CAMERA_MARKERS)


def _is_rejected_camera_name(name: str) -> bool:
    return _is_iphone_camera_name(name) or _is_virtual_camera_name(name)


def _is_builtin_camera_name(name: str) -> bool:
    lowered = name.casefold()
    return any(marker in lowered for marker in BUILTIN_CAMERA_MARKERS)


class CameraFeed:
    def __init__(self, width: int, height: int, index: int = 0) -> None:
        self.width = width
        self.height = height
        self.index = index
        self.device_name: str | None = None
        self.device_names: list[str] = []
        self.available = False
        self.error: str | None = None
        self._cv2 = None
        self._cap = None

        try:
            import cv2
        except ModuleNotFoundError as exc:
            self.error = str(exc)
            return

        self._cv2 = cv2
        if not hasattr(cv2, "VideoCapture"):
            self.error = "OpenCV camera API is unavailable; reinstall opencv-contrib-python"
            return

        self.device_names = mac_camera_device_names()
        manual_index = env_camera_index()
        allow_iphone = os.environ.get(ALLOW_IPHONE_CAMERA_ENV) == "1"
        selected_indexes = [manual_index] if manual_index is not None else camera_index_order(
            index,
            self.device_names,
            allow_iphone=allow_iphone,
        )
        attempts = self._camera_attempts(cv2, selected_indexes)
        for camera_index, backend in attempts:
            self._cap = cv2.VideoCapture(camera_index, backend) if backend is not None else cv2.VideoCapture(camera_index)
            if self._cap.isOpened():
                self.index = camera_index
                self.device_name = self._name_for_index(camera_index)
                break
            self._cap.release()
            self._cap = None

        if self._cap is None or not self._cap.isOpened():
            self.error = self._open_error(manual_index)
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.available = True

    def _camera_attempts(self, cv2, indexes: list[int]) -> list[tuple[int, int | None]]:
        backends: list[int | None] = []
        if hasattr(cv2, "CAP_AVFOUNDATION"):
            backends.append(cv2.CAP_AVFOUNDATION)
        backends.append(None)
        return [(index, backend) for index in indexes for backend in backends]

    def _name_for_index(self, index: int) -> str | None:
        if 0 <= index < len(self.device_names):
            return self.device_names[index]
        return None

    def _open_error(self, manual_index: int | None) -> str:
        detected = ", ".join(f"{index}: {name}" for index, name in enumerate(self.device_names))
        detected_text = f" Detected cameras: {detected}." if detected else ""
        if manual_index is not None:
            return (
                f"camera index {manual_index} could not be opened; try another {CAMERA_INDEX_ENV} value "
                "or allow Camera permission for Python/Terminal."
                f"{detected_text}"
            )
        return (
            "built-in camera could not be opened; iPhone/Continuity and virtual cameras are skipped by default. "
            f"Set {CAMERA_INDEX_ENV}=1 to choose a specific Mac camera, or allow Camera permission for Python/Terminal."
            f"{detected_text}"
        )

    def read_rgb(self):
        if not self.available or self._cap is None or self._cv2 is None:
            return None

        ok, frame = self._cap.read()
        if not ok:
            return None

        frame = self._cv2.resize(frame, (self.width, self.height))
        frame = self._cv2.flip(frame, 1)
        return self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()


def frame_to_surface(rgb_frame):
    import numpy as np
    import pygame

    return pygame.surfarray.make_surface(np.swapaxes(rgb_frame, 0, 1))
