from __future__ import annotations

from dataclasses import dataclass

from .config import FEVER_MULTIPLIER, GOOD_WINDOW, PERFECT_WINDOW


@dataclass(frozen=True)
class SliceResult:
    judgement: str
    points: int
    combo: int
    time_offset: float | None


class ScoreKeeper:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.hits = 0
        self.perfect = 0
        self.good = 0
        self.misses = 0
        self.fever_uses = 0
        self.fever_gauge = 0.0

    def register_slice(self, time_offset: float | None, fever_active: bool = False) -> SliceResult:
        offset_abs = abs(time_offset) if time_offset is not None else None
        if offset_abs is not None and offset_abs <= PERFECT_WINDOW:
            judgement = "Perfect"
            base_points = 100
            self.perfect += 1
            gauge_gain = 0.13
        elif offset_abs is not None and offset_abs <= GOOD_WINDOW:
            judgement = "Good"
            base_points = 70
            self.good += 1
            gauge_gain = 0.09
        else:
            judgement = "Good"
            base_points = 45
            self.good += 1
            gauge_gain = 0.06

        self.hits += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)

        combo_bonus = min(self.combo // 10, 12) * 5
        multiplier = FEVER_MULTIPLIER if fever_active else 1
        points = (base_points + combo_bonus) * multiplier
        self.score += points
        self.fever_gauge = min(1.0, self.fever_gauge + gauge_gain)

        return SliceResult(judgement, points, self.combo, time_offset)

    def register_miss(self) -> None:
        self.misses += 1
        self.combo = 0
        self.fever_gauge = max(0.0, self.fever_gauge - 0.04)

    def can_trigger_fever(self) -> bool:
        return self.fever_gauge >= 1.0

    def trigger_fever(self) -> bool:
        if not self.can_trigger_fever():
            return False
        self.fever_gauge = 0.0
        self.fever_uses += 1
        return True

    def register_fever_clear(self, fruit_count: int) -> int:
        if fruit_count <= 0:
            return 0
        self.hits += fruit_count
        self.combo += fruit_count
        self.max_combo = max(self.max_combo, self.combo)
        points = 40 * fruit_count * FEVER_MULTIPLIER
        self.score += points
        return points

    def accuracy(self) -> float:
        attempts = self.hits + self.misses
        if attempts == 0:
            return 0.0
        weighted_hits = self.perfect + self.good * 0.72
        return weighted_hits / attempts

    def grade(self) -> str:
        accuracy = self.accuracy()
        if accuracy >= 0.94 and self.misses <= 2:
            return "S"
        if accuracy >= 0.7:
            return "A"
        if accuracy >= 0.6:
            return "B"
        if accuracy >= 0.48:
            return "C"
        return "D"
