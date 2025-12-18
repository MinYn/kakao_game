import random
import unittest

from games.adventure import AdventureGame, PetProfile


class AdventureGameTestCase(unittest.TestCase):
    def test_pet_profile_is_deterministic(self):
        first = PetProfile.from_user_id("user-123")
        second = PetProfile.from_user_id("user-123")
        other = PetProfile.from_user_id("another-user")

        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_activity_flow_returns_success_message(self):
        game = AdventureGame(user_id="tester")
        start_message = game.start()
        self.assertIn("펫 모험", start_message)

        random.seed(0)
        response = game.process_command("산책")
        self.assertIn("활동", response)
        self.assertIn("현재 골드", response)

    def test_growth_cost_increases(self):
        game = AdventureGame(user_id="tester")
        game.start()
        base_cost = game._calculate_cost()
        game.current_level = 2
        next_cost = game._calculate_cost()
        self.assertGreaterEqual(next_cost, base_cost)


if __name__ == "__main__":
    unittest.main()
