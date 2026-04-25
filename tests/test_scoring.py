import unittest

from game.scoring import ScoreKeeper


class ScoringTests(unittest.TestCase):
    def test_scoring_perfect_builds_combo_and_gauge(self):
        score = ScoreKeeper()
        result = score.register_slice(0.02)
        self.assertEqual(result.judgement, "Perfect")
        self.assertEqual(score.combo, 1)
        self.assertEqual(score.score, 100)
        self.assertGreater(score.fever_gauge, 0)

    def test_miss_breaks_combo(self):
        score = ScoreKeeper()
        score.register_slice(0.02)
        score.register_miss()
        self.assertEqual(score.combo, 0)
        self.assertEqual(score.misses, 1)

    def test_fever_clear_adds_points_and_combo(self):
        score = ScoreKeeper()
        points = score.register_fever_clear(3)
        self.assertEqual(points, 240)
        self.assertEqual(score.combo, 3)
        self.assertEqual(score.score, 240)

if __name__ == "__main__":
    unittest.main()
