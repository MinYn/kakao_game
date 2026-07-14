import random
import tempfile
import unittest
from unittest.mock import patch

from games.adventure import AdventureGame, ExplorerProfile
from gold_system import GoldSystem


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

    def test_ship_codex_tracks_rarity_as_collection_only(self):
        game = AdventureGame(user_id="tester")
        game.start()

        ship = game._get_ship_by_id("comet_scout")
        self.assertIsNotNone(ship)

        result = game._grant_ship_to_collection(ship)
        self.assertTrue(result["is_new"])
        self.assertEqual(result["count"], 1)

        duplicate = game._grant_ship_to_collection(ship)
        self.assertFalse(duplicate["is_new"])
        self.assertEqual(duplicate["count"], 2)

        response = game.process_command("도감")
        self.assertIn("우주선 도감", response)
        self.assertIn("코멧 스카우트 x2", response)
        self.assertIn("보상/성공률에 영향을 주지 않습니다", response)

    def test_collection_rarity_does_not_change_success_rate(self):
        game = AdventureGame(user_id="tester")
        game.start()
        activity = game._get_activity_type("정찰")
        self.assertIsNotNone(activity)

        game.current_level = 0
        base_rate = game._calculate_success_rate(activity)
        ship = game._get_ship_by_id("event_horizon")
        self.assertIsNotNone(ship)
        game._grant_ship_to_collection(ship)

        self.assertEqual(game._calculate_success_rate(activity), base_rate)

    def test_ship_collection_persists_in_gold_system(self):
        with tempfile.NamedTemporaryFile() as db_file:
            point_system = GoldSystem(db_file.name)
            game = AdventureGame(user_id="tester", point_system=point_system)
            game.start()
            ship = game._get_ship_by_id("event_horizon")
            self.assertIsNotNone(ship)

            first = game._grant_ship_to_collection(ship)
            second = game._grant_ship_to_collection(ship)

            self.assertTrue(first["is_new"])
            self.assertFalse(second["is_new"])
            self.assertEqual(second["count"], 2)
            records = point_system.get_ship_collection("tester")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["ship_id"], "event_horizon")
            self.assertEqual(records[0]["count"], 2)
            self.assertIsNotNone(records[0]["first_acquired_at"])
            self.assertIsNotNone(records[0]["last_acquired_at"])

    def test_enhancement_near_miss_preserves_level(self):
        with tempfile.NamedTemporaryFile() as db_file:
            point_system = GoldSystem(db_file.name)
            game = AdventureGame(user_id="tester", point_system=point_system)
            game.start()
            game.current_level = 2
            point_system.set_enhancement_level("tester", 2)
            point_system.set_gold("tester", 1_000)

            success_rate = game._calculate_success_rate()
            near_miss_roll = (success_rate + 1.0) / 100
            with patch("games.adventure.random.random", return_value=near_miss_roll):
                response = game._enhance()

            self.assertIn("아슬아슬하게 버텼습니다", response)
            self.assertEqual(game.current_level, 2)
            self.assertEqual(point_system.get_enhancement_level("tester"), 2)

    def test_clutch_success_message_when_roll_barely_passes(self):
        with tempfile.NamedTemporaryFile() as db_file:
            point_system = GoldSystem(db_file.name)
            game = AdventureGame(user_id="tester", point_system=point_system)
            game.start()
            point_system.set_gold("tester", 1_000)

            success_rate = game._calculate_success_rate()
            clutch_roll = (success_rate - 1.0) / 100
            with patch("games.adventure.random.random", return_value=clutch_roll):
                response = game._enhance()

            self.assertIn("아슬아슬 턱걸이 성공", response)
            self.assertEqual(game.current_level, 1)

    def test_loot_reward_roll_returns_gold_drop(self):
        game = AdventureGame(user_id="tester")
        game.start()

        with patch("games.adventure.random.random", return_value=0.0), patch(
            "games.adventure.random.randint", return_value=42
        ):
            loot_reward = game._try_roll_loot_reward()

        self.assertIsNotNone(loot_reward)
        self.assertEqual(loot_reward["loot"].name, "고철 부품 상자")
        self.assertEqual(loot_reward["amount"], 42)


if __name__ == "__main__":
    unittest.main()
