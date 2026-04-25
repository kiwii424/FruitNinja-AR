import unittest

from game.rhythm import BeatEvent, RhythmSpawner, default_events


class RhythmTests(unittest.TestCase):
    def test_default_events_are_sorted(self):
        events = default_events(duration=4, bpm=120)
        self.assertTrue(events)
        self.assertEqual(list(events), sorted(events, key=lambda event: event.timestamp))

    def test_spawner_emits_before_target_time(self):
        event = BeatEvent(timestamp=2.0, strength=0.5, index=0)
        spawner = RhythmSpawner((event,), lead_time=1.0, seed=1)
        fruits, next_id = spawner.due_fruits(game_time=0.5, width=800, height=600, next_fruit_id=0)
        self.assertEqual(fruits, [])
        self.assertEqual(next_id, 0)

        fruits, next_id = spawner.due_fruits(game_time=1.0, width=800, height=600, next_fruit_id=0)
        self.assertEqual(len(fruits), 1)
        self.assertEqual(next_id, 1)
        self.assertEqual(fruits[0].target_time, 2.0)

    def test_spawner_increments_ids_for_multiple_events(self):
        events = (
            BeatEvent(timestamp=2.0, strength=0.5, index=0),
            BeatEvent(timestamp=2.1, strength=0.5, index=1),
        )
        spawner = RhythmSpawner(events, lead_time=1.0, seed=1)
        fruits, next_id = spawner.due_fruits(game_time=1.1, width=800, height=600, next_fruit_id=0)
        self.assertEqual(len(fruits), 2)
        self.assertEqual(next_id, 2)
        self.assertEqual([fruit.fruit_id for fruit in fruits], [0, 1])

    def test_spawner_keeps_low_speed_multiplier(self):
        event = BeatEvent(timestamp=2.0, strength=0.5, index=0)
        spawner = RhythmSpawner((event,), lead_time=4.0, speed_multiplier=0.15, seed=1)
        fruits, _ = spawner.due_fruits(game_time=-2.0, width=800, height=600, next_fruit_id=0)
        self.assertEqual(len(fruits), 1)
        self.assertAlmostEqual(fruits[0].gravity_scale, 0.15)


if __name__ == "__main__":
    unittest.main()
