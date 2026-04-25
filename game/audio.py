from __future__ import annotations

import math


class SfxPlayer:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.hit = None
        self.start = None
        self.end = None
        if not enabled:
            return

        try:
            import numpy as np
            import pygame
        except ModuleNotFoundError:
            self.enabled = False
            return

        init = pygame.mixer.get_init()
        if init is None:
            self.enabled = False
            return

        sample_rate, _, channels = init
        self.hit = self._make_sound(np, pygame, sample_rate, channels, ((880, 0.055), (1320, 0.035)), 0.24)
        self.start = self._make_sound(np, pygame, sample_rate, channels, ((523, 0.10), (784, 0.12), (1046, 0.16)), 0.22)
        self.end = self._make_sound(np, pygame, sample_rate, channels, ((784, 0.12), (622, 0.12), (392, 0.20)), 0.26)

    def _make_sound(self, np, pygame, sample_rate: int, channels: int, notes: tuple[tuple[int, float], ...], volume: float):
        wave_parts = []
        for frequency, duration in notes:
            count = max(1, int(sample_rate * duration))
            t = np.linspace(0.0, duration, count, endpoint=False)
            envelope = np.exp(-5.0 * t / max(duration, 0.001))
            tone = np.sin(2.0 * math.pi * frequency * t) * envelope
            wave_parts.append(tone)
        data = np.concatenate(wave_parts)
        data = np.clip(data * volume * 32767, -32768, 32767).astype(np.int16)
        if channels == 2:
            data = np.column_stack((data, data))
        return pygame.sndarray.make_sound(data)

    def play_hit(self) -> None:
        self._play(self.hit)

    def play_start(self) -> None:
        self._play(self.start)

    def play_end(self) -> None:
        self._play(self.end)

    def _play(self, sound) -> None:
        if self.enabled and sound is not None:
            sound.play()
