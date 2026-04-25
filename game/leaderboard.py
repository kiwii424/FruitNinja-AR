from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import LEADERBOARD_PATH


@dataclass(frozen=True)
class LeaderboardEntry:
    name: str
    score: int
    grade: str
    max_combo: int
    accuracy: float
    timestamp: str


class Leaderboard:
    def __init__(self, path: str = LEADERBOARD_PATH, limit: int = 10) -> None:
        self.path = Path(path)
        self.limit = limit

    def load(self) -> list[LeaderboardEntry]:
        if not self.path.exists():
            return []
        try:
            raw_entries = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        entries: list[LeaderboardEntry] = []
        for item in raw_entries:
            try:
                entries.append(
                    LeaderboardEntry(
                        name=str(item["name"]),
                        score=int(item["score"]),
                        grade=str(item["grade"]),
                        max_combo=int(item["max_combo"]),
                        accuracy=float(item["accuracy"]),
                        timestamp=str(item["timestamp"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return self._dedupe_highest(entries)

    def add_score(self, name: str, score, timestamp: datetime | None = None) -> tuple[list[LeaderboardEntry], bool]:
        clean_name = _clean_name(name)
        now = timestamp or datetime.now(timezone.utc)
        entry = LeaderboardEntry(
            name=clean_name,
            score=int(score.score),
            grade=score.grade(),
            max_combo=int(score.max_combo),
            accuracy=round(score.accuracy(), 4),
            timestamp=now.isoformat(timespec="seconds"),
        )
        existing_entries = self.load()
        name_key = clean_name.casefold()
        previous = next((item for item in existing_entries if item.name.casefold() == name_key), None)
        is_new_high = previous is None or entry.score > previous.score

        if is_new_high:
            entries = [item for item in existing_entries if item.name.casefold() != name_key]
            entries.append(entry)
        else:
            entries = existing_entries

        entries = self._sort(entries)[: self.limit]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(item) for item in entries], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return entries, is_new_high

    def _sort(self, entries: list[LeaderboardEntry]) -> list[LeaderboardEntry]:
        return sorted(entries, key=lambda item: (item.score, item.max_combo, item.accuracy), reverse=True)

    def _dedupe_highest(self, entries: list[LeaderboardEntry]) -> list[LeaderboardEntry]:
        best_by_name: dict[str, LeaderboardEntry] = {}
        for entry in self._sort(entries):
            key = entry.name.casefold()
            if key not in best_by_name:
                best_by_name[key] = entry
        return self._sort(list(best_by_name.values()))


def _clean_name(name: str) -> str:
    cleaned = " ".join(name.strip().split())
    if not cleaned:
        return "Player"
    return cleaned[:16]
