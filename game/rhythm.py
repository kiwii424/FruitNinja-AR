from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

from .config import (
    DEFAULT_BPM,
    DEFAULT_DURATION,
    ROCK_TYPES,
    GRAVITY,
    HIT_LINE_Y_RATIO,
    SPAWN_LEAD_TIME,
)
from .entities import Rock


@dataclass(frozen=True)
class BeatEvent:
    timestamp: float
    strength: float = 0.5
    index: int = 0


@dataclass(frozen=True)
class MusicAnalysis:
    path: str | None
    title: str
    duration: float
    tempo: float
    events: tuple[BeatEvent, ...]


def default_events(duration: float = DEFAULT_DURATION, bpm: float = DEFAULT_BPM) -> tuple[BeatEvent, ...]:
    interval = 60.0 / bpm
    events: list[BeatEvent] = []
    timestamp = 1.0
    index = 0
    while timestamp <= duration:
        strength = 0.88 if index % 8 == 0 else 0.62 if index % 4 == 0 else 0.46
        events.append(BeatEvent(timestamp=timestamp, strength=strength, index=index))
        timestamp += interval
        index += 1
    return tuple(events)


def default_analysis() -> MusicAnalysis:
    return MusicAnalysis(
        path=None,
        title="Default Beat",
        duration=DEFAULT_DURATION,
        tempo=float(DEFAULT_BPM),
        events=default_events(),
    )


def analyze_music(path: str) -> MusicAnalysis:
    try:
        import librosa
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError("librosa and numpy are required for music analysis") from exc

    music_path = Path(path)
    y, sr = librosa.load(str(music_path), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    if duration <= 0:
        raise RuntimeError("music file has no playable duration")

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, units="frames")
    tempo_value = float(np.asarray(tempo).reshape(-1)[0]) if np.asarray(tempo).size else float(DEFAULT_BPM)

    if len(beat_frames) == 0:
        beat_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="frames")

    times = librosa.frames_to_time(beat_frames, sr=sr)
    if len(times) == 0:
        return MusicAnalysis(
            path=str(music_path),
            title=music_path.stem,
            duration=duration,
            tempo=tempo_value,
            events=default_events(duration=duration, bpm=DEFAULT_BPM),
        )

    frame_strengths = onset_env[beat_frames]
    max_strength = float(np.max(frame_strengths)) if len(frame_strengths) else 1.0
    if max_strength <= 0:
        max_strength = 1.0

    events: list[BeatEvent] = []
    for index, timestamp in enumerate(times):
        timestamp_value = float(timestamp)
        if timestamp_value < 0.25 or timestamp_value > duration + 0.1:
            continue
        strength = max(0.25, min(1.0, float(frame_strengths[index]) / max_strength))
        events.append(BeatEvent(timestamp=timestamp_value, strength=strength, index=index))

    if not events:
        events = list(default_events(duration=duration, bpm=DEFAULT_BPM))

    return MusicAnalysis(
        path=str(music_path),
        title=music_path.stem,
        duration=duration,
        tempo=tempo_value,
        events=tuple(events),
    )


class RhythmSpawner:
    def __init__(
        self,
        events: tuple[BeatEvent, ...],
        lead_time: float = SPAWN_LEAD_TIME,
        speed_multiplier: float = 1.0,
        seed: int | None = None,
    ) -> None:
        self.events = tuple(sorted(events, key=lambda event: event.timestamp))
        self.lead_time = lead_time
        self.speed_multiplier = max(0.05, speed_multiplier)
        self._next_index = 0
        self._rng = random.Random(seed)

    def reset(self) -> None:
        self._next_index = 0

    @property
    def done(self) -> bool:
        return self._next_index >= len(self.events)

    def due_rocks(
        self,
        game_time: float,
        width: int,
        height: int,
        next_rock_id: int,
    ) -> tuple[list[Rock], int]:
        rocks: list[Rock] = []
        while self._next_index < len(self.events):
            event = self.events[self._next_index]
            if event.timestamp - self.lead_time > game_time:
                break
            event_rocks = self._build_rocks(event, game_time, width, height, next_rock_id)
            rocks.extend(event_rocks)
            next_rock_id += len(event_rocks)
            self._next_index += 1
        return rocks, next_rock_id

    def _build_rocks(
        self,
        event: BeatEvent,
        game_time: float,
        width: int,
        height: int,
        next_rock_id: int,
    ) -> list[Rock]:
        count = 2 if event.strength >= 0.84 and event.index % 4 == 0 else 1
        rocks: list[Rock] = []
        for offset in range(count):
            spec = self._rng.choice(ROCK_TYPES)
            radius = float(spec["radius"]) * (0.92 + event.strength * 0.22)
            target_x = self._lane_x(width, event.index + offset * 2)
            target_y = height * HIT_LINE_Y_RATIO + self._rng.uniform(-76, 76)
            start_x = target_x + self._rng.uniform(-110, 110)
            start_y = -radius - self._rng.uniform(20, 120)
            flight_time = max(0.72, event.timestamp - game_time)

            vx = (target_x - start_x) / flight_time
            gravity = GRAVITY * self.speed_multiplier
            vy = (target_y - start_y - 0.5 * gravity * flight_time * flight_time) / flight_time
            if not math.isfinite(vy):
                vy = 0.0

            rocks.append(
                Rock(
                    rock_id=next_rock_id + offset,
                    kind=str(spec["name"]),
                    x=start_x,
                    y=start_y,
                    vx=vx,
                    vy=vy,
                    radius=radius,
                    color=spec["color"],
                    accent=spec["accent"],
                    target_time=event.timestamp,
                    strength=event.strength,
                    gravity_scale=self.speed_multiplier,
                    spin=self._rng.uniform(-4.2, 4.2),
                )
            )
        return rocks

    def _lane_x(self, width: int, index: int) -> float:
        lane_count = 7
        lane = index % lane_count
        lane_width = width / (lane_count + 1)
        return lane_width * (lane + 1) + self._rng.uniform(-34, 34)
