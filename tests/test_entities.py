import unittest

from game.entities import distance_point_to_segment


class EntityTests(unittest.TestCase):
    def test_distance_point_to_segment_middle_projection(self):
        self.assertEqual(distance_point_to_segment(5, 3, 0, 0, 10, 0), 3)

    def test_distance_point_to_segment_endpoint_projection(self):
        self.assertEqual(round(distance_point_to_segment(-3, 4, 0, 0, 10, 0), 4), 5.0)


if __name__ == "__main__":
    unittest.main()
