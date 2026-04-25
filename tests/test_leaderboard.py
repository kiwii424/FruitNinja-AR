import tempfile
import unittest
from pathlib import Path

from game.leaderboard import Leaderboard
from game.scoring import ScoreKeeper


class LeaderboardTests(unittest.TestCase):
    def test_add_score_sorts_and_trims_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leaderboard.json"
            board = Leaderboard(str(path), limit=2)

            low = ScoreKeeper()
            low.score = 100
            high = ScoreKeeper()
            high.score = 300

            board.add_score("  Very Long Player Name  ", low)
            entries, is_new_high = board.add_score("Ace", high)

            self.assertTrue(is_new_high)
            self.assertEqual(entries[0].name, "Ace")
            self.assertEqual(entries[0].score, 300)
            self.assertEqual(entries[1].name, "Very Long Player")

    def test_same_player_keeps_only_highest_score(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leaderboard.json"
            board = Leaderboard(str(path), limit=10)

            high = ScoreKeeper()
            high.score = 500
            low = ScoreKeeper()
            low.score = 200
            better = ScoreKeeper()
            better.score = 650

            entries, is_new_high = board.add_score("Mika", high)
            self.assertTrue(is_new_high)
            self.assertEqual(len(entries), 1)

            entries, is_new_high = board.add_score("mika", low)
            self.assertFalse(is_new_high)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].score, 500)

            entries, is_new_high = board.add_score("MIKA", better)
            self.assertTrue(is_new_high)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].score, 650)


if __name__ == "__main__":
    unittest.main()
