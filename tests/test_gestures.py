import unittest

from game.gestures import LandmarkPoint, classify_pose


def _landmarks(index_up=True, middle_up=False, ring_up=False, pinky_up=False, thumb_up=False):
    points = [LandmarkPoint(0.5, 0.7) for _ in range(21)]
    points[0] = LandmarkPoint(0.5, 0.8)
    points[5] = LandmarkPoint(0.42, 0.58)
    points[9] = LandmarkPoint(0.50, 0.56)
    points[13] = LandmarkPoint(0.58, 0.58)
    points[17] = LandmarkPoint(0.66, 0.62)

    finger_pairs = {
        8: (6, index_up),
        12: (10, middle_up),
        16: (14, ring_up),
        20: (18, pinky_up),
    }
    for tip, (pip, up) in finger_pairs.items():
        points[pip] = LandmarkPoint(points[tip].x, 0.50)
        points[tip] = LandmarkPoint(points[tip].x, 0.40 if up else 0.58)

    points[3] = LandmarkPoint(0.46, 0.70)
    points[4] = LandmarkPoint(0.30 if thumb_up else 0.47, 0.68)
    return points


class GestureTests(unittest.TestCase):
    def test_classify_index_sword(self):
        mode, count = classify_pose(_landmarks(index_up=True))
        self.assertEqual(mode, "INDEX_SWORD")
        self.assertGreaterEqual(count, 1)

    def test_classify_open_palm(self):
        mode, count = classify_pose(
            _landmarks(index_up=True, middle_up=True, ring_up=True, pinky_up=True, thumb_up=True)
        )
        self.assertEqual(mode, "OPEN_PALM")
        self.assertGreaterEqual(count, 4)

    def test_classify_fist(self):
        mode, count = classify_pose(
            _landmarks(index_up=False, middle_up=False, ring_up=False, pinky_up=False, thumb_up=False)
        )
        self.assertEqual(mode, "FIST")
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
