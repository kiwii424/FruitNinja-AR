from __future__ import annotations

import os
import traceback
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def suppress_native_stderr():
    if os.environ.get("ARFN_SHOW_NATIVE_LOGS") == "1":
        yield
        return

    saved_stderr = os.dup(2)
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            os.dup2(devnull.fileno(), 2)
            yield
    finally:
        os.dup2(saved_stderr, 2)
        os.close(saved_stderr)


def main() -> int:
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    os.environ.setdefault("GLOG_minloglevel", "3")
    os.environ.setdefault("ABSL_MIN_LOG_LEVEL", "3")

    try:
        with suppress_native_stderr():
            from game.app import run
    except ModuleNotFoundError as exc:
        missing = exc.name or "a dependency"
        print(f"Missing dependency: {missing}")
        print("Install project dependencies with: python3 -m pip install -r requirements.txt")
        return 1

    try:
        with suppress_native_stderr():
            return run()
    except Exception:
        crash_log = Path("data/crash.log")
        crash_log.parent.mkdir(parents=True, exist_ok=True)
        crash_log.write_text(traceback.format_exc(), encoding="utf-8")
        print(f"The game crashed. Details were saved to {crash_log}")
        print(crash_log.read_text(encoding="utf-8"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
