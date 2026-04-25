import unittest
from unittest.mock import patch

from game.camera import camera_index_order, parse_system_profiler_camera_names


class CameraSelectionTests(unittest.TestCase):
    def test_prefers_builtin_camera_over_iphone(self):
        order = camera_index_order(0, ["Meredith iPhone Camera", "FaceTime HD Camera"])
        self.assertEqual(order[0], 1)
        self.assertNotIn(0, order)

    def test_can_allow_iphone_camera_explicitly(self):
        order = camera_index_order(0, ["Meredith iPhone Camera", "FaceTime HD Camera"], allow_iphone=True)
        self.assertIn(0, order)
        self.assertEqual(order[0], 1)

    def test_falls_back_to_preferred_index_without_device_names(self):
        self.assertEqual(camera_index_order(2, []), [2, 0, 1, 3])

    def test_mac_without_device_names_tries_non_default_camera_first(self):
        with patch("game.camera.platform.system", return_value="Darwin"):
            self.assertEqual(camera_index_order(0, []), [1, 0, 2, 3])

    def test_parses_system_profiler_json_names(self):
        output = """
        {
          "SPCameraDataType": [
            {"_name": "Meredith iPhone Camera"},
            {"_name": "FaceTime HD Camera"}
          ]
        }
        """
        self.assertEqual(
            parse_system_profiler_camera_names(output),
            ["Meredith iPhone Camera", "FaceTime HD Camera"],
        )


if __name__ == "__main__":
    unittest.main()
