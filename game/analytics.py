from __future__ import annotations

import math

from .config import GOOD_WINDOW


class AnalyticsTracker:
    """Collects per-event gameplay data for DDA and the post-game radar chart."""

    _DDA_WINDOW     = 15.0   # seconds of history used for DDA
    _MISS_RATE_HIGH = 0.42   # above this  → ease down spawn density
    _MISS_RATE_LOW  = 0.18   # below this  → ease up  spawn density
    _EASE           = 0.08   # lerp step per DDA update

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._hits:    list[tuple[float, float | None, str]] = []  # (t, offset, judgement)
        self._misses:  list[float]                           = []  # game_time
        self._catches: list[tuple[float, str]]               = []  # (t, variant)
        self._spawn_gate = 1.0

    # ── event recording ────────────────────────────────────────────────────────

    def record_hit(self, game_time: float, time_offset: float | None, judgement: str) -> None:
        self._hits.append((game_time, time_offset, judgement))
        self._update_dda(game_time)

    def record_miss(self, game_time: float) -> None:
        self._misses.append(game_time)
        self._update_dda(game_time)

    def record_catch(self, game_time: float, variant: str) -> None:
        self._catches.append((game_time, variant))

    # ── DDA ────────────────────────────────────────────────────────────────────

    @property
    def spawn_gate(self) -> float:
        """Probability [0.55, 1.0] that a spawnable fruit is actually added.
        Decreases when the player is missing frequently; recovers as they improve."""
        return self._spawn_gate

    def _update_dda(self, now: float) -> None:
        since = now - self._DDA_WINDOW
        recent_hits   = sum(1 for t, _, _ in self._hits   if t >= since)
        recent_misses = sum(1 for t        in self._misses if t >= since)
        miss_rate = recent_misses / max(1, recent_hits + recent_misses)

        if miss_rate > self._MISS_RATE_HIGH:
            target = max(0.55, self._spawn_gate - 0.05)
        elif miss_rate < self._MISS_RATE_LOW:
            target = min(1.00, self._spawn_gate + 0.02)
        else:
            target = self._spawn_gate

        self._spawn_gate += (target - self._spawn_gate) * self._EASE

    # ── radar stats ────────────────────────────────────────────────────────────

    def radar_stats(self, max_combo: int) -> dict[str, float]:
        """Return 5 normalised [0, 1] scores for the radar chart."""
        hits   = len(self._hits)
        misses = len(self._misses)

        precision = hits / max(1, hits + misses)

        perfects = sum(1 for _, _, j in self._hits if j == "Perfect")
        rhythm   = perfects / max(1, hits)

        dexterity = min(1.0, max_combo / 25.0)

        offsets   = [abs(o) for _, o, _ in self._hits if o is not None]
        avg_off   = sum(offsets) / len(offsets) if offsets else GOOD_WINDOW
        reaction  = 1.0 - min(1.0, avg_off / GOOD_WINDOW)

        catch = min(1.0, len(self._catches) / 5.0)

        return {
            "Precision": precision,
            "Rhythm":    rhythm,
            "Dexterity": dexterity,
            "Reaction":  reaction,
            "Catch":     catch,
        }


# ── standalone radar chart renderer (pure pygame, no matplotlib) ───────────────

def draw_radar_chart(
    surface,
    cx: int,
    cy: int,
    radius: int,
    stats: dict[str, float],
    font,
    *,
    grid_color:  tuple = (55, 75, 100),
    fill_color:  tuple = (255, 160, 30),
    label_color: tuple = (190, 205, 220),
) -> None:
    import pygame

    labels = list(stats.keys())
    values = list(stats.values())
    n      = len(labels)

    # Angles: first axis at top (270°), rotating clockwise
    angles = [math.radians(270 + i * 360 / n) for i in range(n)]

    # Draw concentric grid polygons
    for level in (0.25, 0.5, 0.75, 1.0):
        pts = [
            (int(cx + radius * level * math.cos(a)),
             int(cy + radius * level * math.sin(a)))
            for a in angles
        ]
        pygame.draw.polygon(surface, grid_color, pts, 1)

    # Draw axis lines
    for a in angles:
        end = (int(cx + radius * math.cos(a)), int(cy + radius * math.sin(a)))
        pygame.draw.line(surface, grid_color, (cx, cy), end, 1)

    # Draw filled player-data polygon
    data_pts = [
        (int(cx + radius * v * math.cos(a)),
         int(cy + radius * v * math.sin(a)))
        for v, a in zip(values, angles)
    ]
    fill_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(fill_surf, (*fill_color, 55), data_pts)
    surface.blit(fill_surf, (0, 0))
    pygame.draw.polygon(surface, fill_color, data_pts, 2)

    # Draw axis labels + percentage value
    for label, angle, value in zip(labels, angles, values):
        offset = radius + 22
        lx = int(cx + offset * math.cos(angle))
        ly = int(cy + offset * math.sin(angle))

        name_surf = font.render(label, True, label_color)
        name_rect = name_surf.get_rect(center=(lx, ly))
        surface.blit(name_surf, name_rect)

        pct_surf = font.render(f"{int(value * 100)}%", True, fill_color)
        pct_rect = pct_surf.get_rect(center=(lx, ly + 16))
        surface.blit(pct_surf, pct_rect)
