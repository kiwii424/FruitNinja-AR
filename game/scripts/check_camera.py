from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.camera import CAMERA_INDEX_ENV, CameraFeed, mac_camera_device_names


def main() -> int:
    if len(sys.argv) > 1:
        import os

        os.environ[CAMERA_INDEX_ENV] = sys.argv[1]

    names = mac_camera_device_names()
    if names:
        print("detected cameras:")
        for index, name in enumerate(names):
            print(f"  {index}: {name}")
    else:
        print("detected cameras: unavailable from macOS")

    camera = CameraFeed(640, 360)
    print(f"available: {camera.available}")
    print(f"index: {camera.index}")
    print(f"device: {camera.device_name or 'unknown'}")
    print(f"error: {camera.error}")
    frame = camera.read_rgb()
    print(f"frame: {None if frame is None else frame.shape}")
    camera.close()
    return 0 if camera.available and frame is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
