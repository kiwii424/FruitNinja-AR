import unittest

from game.entities import PikminRunner


class PikminRunnerTests(unittest.TestCase):
    def test_runner_is_catchable_near_point(self):
        runner = PikminRunner(
            runner_id=1,
            variant="Red",
            x=100,
            y=100,
            vx=0,
            vy=0,
            color=(255, 0, 0),
            target_x=200,
            target_y=100,
            wiggle=0,
        )
        self.assertTrue(runner.catchable_by((120, 110)))
        self.assertFalse(runner.catchable_by((300, 300)))

    def test_runner_updates_with_speed_scale(self):
        runner = PikminRunner(
            runner_id=2,
            variant="Blue",
            x=100,
            y=100,
            vx=10,
            vy=0,
            color=(0, 0, 255),
            target_x=200,
            target_y=100,
            wiggle=0,
            speed_scale=0.2,
        )
        runner.update(0.5)
        self.assertGreater(runner.x, 100)
        self.assertLess(runner.ttl, 9.0)


if __name__ == "__main__":
    unittest.main()
