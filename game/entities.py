from __future__ import annotations

import math
from dataclasses import dataclass

from .config import GRAVITY, PIKMIN_ACCELERATION, PIKMIN_MAX_SPEED, PIKMIN_WIGGLE_X, PIKMIN_WIGGLE_Y


def distance_point_to_segment(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    length_sq = abx * abx + aby * aby
    if length_sq == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / length_sq))
    closest_x = ax + abx * t
    closest_y = ay + aby * t
    return math.hypot(px - closest_x, py - closest_y)


@dataclass
class Fruit:
    fruit_id: int
    kind: str
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    color: tuple[int, int, int]
    accent: tuple[int, int, int]
    target_time: float
    strength: float = 0.5
    gravity_scale: float = 1.0
    sliced: bool = False
    rotation: float = 0.0
    spin: float = 0.0

    def update(self, dt: float) -> None:
        self.vy += GRAVITY * self.gravity_scale * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.spin * dt

    def intersects_segment(self, start: tuple[float, float], end: tuple[float, float]) -> bool:
        return distance_point_to_segment(self.x, self.y, start[0], start[1], end[0], end[1]) <= self.radius

    def is_offscreen(self, height: int) -> bool:
        return self.y - self.radius > height + 80

    def draw(self, surface) -> None:
        import pygame

        center = (int(self.x), int(self.y))
        radius = int(self.radius)
        points = []
        sides = 9
        for index in range(sides):
            angle = self.rotation + math.tau * index / sides
            wobble = 0.78 + 0.18 * math.sin(index * 1.9 + self.fruit_id)
            points.append((int(self.x + math.cos(angle) * radius * wobble), int(self.y + math.sin(angle) * radius * wobble)))

        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (232, 235, 240), points, 2)
        crack_color = (38, 43, 50)
        pygame.draw.line(surface, crack_color, (center[0] - radius // 2, center[1] - radius // 5), (center[0], center[1] + radius // 4), 3)
        pygame.draw.line(surface, crack_color, (center[0], center[1] + radius // 4), (center[0] + radius // 2, center[1] - radius // 3), 3)
        highlight_center = (int(self.x - radius * 0.28), int(self.y - radius * 0.35))
        pygame.draw.circle(surface, self.accent, highlight_center, max(4, radius // 6))


@dataclass
class PikminRunner:
    runner_id: int
    variant: str
    x: float
    y: float
    vx: float
    vy: float
    color: tuple[int, int, int]
    target_x: float
    target_y: float
    wiggle: float
    speed_scale: float = 1.0
    caught: bool = False
    ttl: float = 9.0

    def update(self, dt: float) -> None:
        self.ttl -= dt
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = max(1.0, math.hypot(dx, dy))
        acceleration = PIKMIN_ACCELERATION * max(0.1, self.speed_scale)
        self.vx += dx / distance * acceleration * dt
        self.vy += dy / distance * acceleration * dt
        speed = math.hypot(self.vx, self.vy)
        max_speed = PIKMIN_MAX_SPEED * max(0.1, self.speed_scale)
        if speed > max_speed:
            self.vx = self.vx / speed * max_speed
            self.vy = self.vy / speed * max_speed
        self.x += self.vx * dt + math.sin(self.ttl * 12.0 + self.wiggle) * PIKMIN_WIGGLE_X * self.speed_scale * dt
        self.y += self.vy * dt + math.cos(self.ttl * 9.0 + self.wiggle) * PIKMIN_WIGGLE_Y * self.speed_scale * dt

    def escaped(self, width: int, height: int) -> bool:
        return self.ttl <= 0 or self.x < -60 or self.x > width + 60 or self.y < -60 or self.y > height + 60

    def catchable_by(self, point: tuple[int, int] | None, radius: float = 70.0) -> bool:
        if point is None:
            return False
        return math.hypot(self.x - point[0], self.y - point[1]) <= radius

    def draw(self, surface) -> None:
        import pygame

        center = (int(self.x), int(self.y))
        body_rect = pygame.Rect(0, 0, 18, 26)
        body_rect.center = center
        pygame.draw.ellipse(surface, self.color, body_rect)
        pygame.draw.ellipse(surface, (255, 255, 255), body_rect, 2)
        pygame.draw.circle(surface, (20, 24, 28), (center[0] - 4, center[1] - 4), 2)
        pygame.draw.circle(surface, (20, 24, 28), (center[0] + 4, center[1] - 4), 2)
        pygame.draw.line(surface, (79, 166, 88), (center[0], center[1] - 14), (center[0], center[1] - 30), 3)
        leaf = [
            (center[0], center[1] - 31),
            (center[0] + 12, center[1] - 38),
            (center[0] + 8, center[1] - 24),
        ]
        pygame.draw.polygon(surface, (88, 205, 106), leaf)
        pygame.draw.line(surface, (36, 42, 48), (center[0] - 5, center[1] + 12), (center[0] - 10, center[1] + 20), 2)
        pygame.draw.line(surface, (36, 42, 48), (center[0] + 5, center[1] + 12), (center[0] + 10, center[1] + 20), 2)


@dataclass
class SliceSpark:
    x: float
    y: float
    vx: float
    vy: float
    color: tuple[int, int, int]
    ttl: float = 0.45

    def update(self, dt: float) -> None:
        self.ttl -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 360.0 * dt

    def alive(self) -> bool:
        return self.ttl > 0

    def draw(self, surface) -> None:
        import pygame

        alpha = max(0, min(255, int(255 * (self.ttl / 0.45))))
        color = (
            min(255, self.color[0] + 35),
            min(255, self.color[1] + 35),
            min(255, self.color[2] + 35),
            alpha,
        )
        spark_surface = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(spark_surface, color, (6, 6), 5)
        surface.blit(spark_surface, (int(self.x - 6), int(self.y - 6)))
