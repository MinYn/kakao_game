import random
import unittest

from games.adventure import AdventureGame, ExplorerProfile


class AdventureGameTestCase(unittest.TestCase):
    def test_explorer_profile_is_deterministic(self):
        first = ExplorerProfile.from_user_id("user-123")
        second = ExplorerProfile.from_user_id("user-123")
        other = ExplorerProfile.from_user_id("another-user")

        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_activity_flow_returns_success_message(self):
        game = AdventureGame(user_id="tester")
        start_message = game.start()
        self.assertIn("우주 탐험", start_message)

        random.seed(0)
        response = game.process_command("정찰")
        self.assertIn("활동", response)
        self.assertIn("현재 골드", response)

    def test_growth_cost_increases(self):
        game = AdventureGame(user_id="tester")
        game.start()
        base_cost = game._calculate_cost()
        game.current_level = 2
        next_cost = game._calculate_cost()
        self.assertGreaterEqual(next_cost, base_cost)

    def test_ship_grade_increases_with_level(self):
        game = AdventureGame(user_id="tester")
        game.start()

        self.assertEqual(game._get_ship_grade().name, "C급 셔틀")

        game.current_level = 6
        self.assertEqual(game._get_ship_grade().name, "A급 코르벳")

        response = game.process_command("등급")
        self.assertIn("우주선 등급 현황", response)
        self.assertIn("잭팟", response)

    def test_high_grade_reward_is_higher_than_base_reward_floor(self):
        game = AdventureGame(user_id="tester")
        game.start()
        activity = game._get_activity_type("정찰")
        self.assertIsNotNone(activity)

        random.seed(3)
        game.current_level = 0
        base_reward = game._calculate_activity_reward(activity)

        random.seed(3)
        game.current_level = 15
        high_grade_reward = game._calculate_activity_reward(activity)

        self.assertGreater(high_grade_reward, base_reward)


if __name__ == "__main__":
    unittest.main()
