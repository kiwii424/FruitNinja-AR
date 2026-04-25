import unittest

from game.config import CAMERA_GAME_BOTTOM
from game.gestures import map_camera_to_screen


class MappingTests(unittest.TestCase):
    def test_camera_bottom_frame_maps_to_screen_bottom(self):
        self.assertEqual(map_camera_to_screen(0.5, CAMERA_GAME_BOTTOM, (1000, 800))[1], 800)

    def test_camera_below_game_frame_clamps_to_screen_bottom(self):
        self.assertEqual(map_camera_to_screen(0.5, 0.95, (1000, 800))[1], 800)


if __name__ == "__main__":
    unittest.main()
