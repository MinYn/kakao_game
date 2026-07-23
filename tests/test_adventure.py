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
        # 모바일 D0 홈: 출동은 버튼에 있고 본문에는 없을 수 있음
        buttons = game.get_command_buttons()
        self.assertIn("출동", [b["messageText"] for b in buttons])

        # 성공 판정/보상 롤은 통과시키고 이벤트 타입만 고정
        scout = game._get_activity_type("정찰")
        with patch.object(game, "_select_random_activity", return_value=scout), patch(
            "games.adventure.random.random", return_value=0.0
        ):
            response = game.process_command("출동")
        self.assertIn("정찰 성공", response)
        self.assertIn("정찰", response)
        self.assertIn("골드", response)

    def test_legacy_activity_commands_alias_to_mission(self):
        game = AdventureGame(user_id="tester")
        game.start()
        scout = game._get_activity_type("정찰")
        with patch.object(game, "_select_random_activity", return_value=scout) as select_mock, patch(
            "games.adventure.random.random", return_value=0.0
        ):
            for command in ("정찰", "탐사", "구조", "mission", "출동"):
                response = game.process_command(command)
                self.assertIn("정찰", response)
        self.assertEqual(select_mock.call_count, 5)

    def test_mission_excludes_rescue_without_pass(self):
        with tempfile.NamedTemporaryFile() as db_file:
            point_system = GoldSystem(db_file.name)
            game = AdventureGame(user_id="tester", point_system=point_system)
            game.start()
            self.assertEqual(point_system.get_boss_tickets("tester"), 0)

            selected = {game._select_random_activity().name for _ in range(80)}
            self.assertIn("정찰", selected)
            self.assertIn("탐사", selected)
            self.assertNotIn("구조", selected)

    def test_mission_can_select_rescue_with_pass(self):
        with tempfile.NamedTemporaryFile() as db_file:
            point_system = GoldSystem(db_file.name)
            game = AdventureGame(user_id="tester", point_system=point_system)
            game.start()
            point_system.add_boss_ticket("tester", 3, "test grant")

            selected = {game._select_random_activity().name for _ in range(200)}
            self.assertIn("구조", selected)

    def test_mission_button_is_unified(self):
        game = AdventureGame(user_id="tester")
        game.start()
        buttons = game.get_command_buttons()
        labels = [b["label"] for b in buttons]
        messages = [b["messageText"] for b in buttons]
        # D0 홈: 성장/출동/도감/상태 (정확히 4)
        self.assertEqual(len(buttons), 4)
        self.assertIn("🚀 출동", labels)
        self.assertIn("출동", messages)
        self.assertNotIn("정찰", messages)
        self.assertNotIn("탐사", messages)
        self.assertNotIn("구조", messages)

    def test_growth_cost_increases(self):
        game = AdventureGame(user_id="tester")
        game.start()
        base_cost = game._calculate_cost()
        game.ship_progress = game.ship_progress.with_body_enhance(2)
        game._sync_level_from_progress()
        next_cost = game._calculate_cost()
        self.assertGreaterEqual(next_cost, base_cost)

    def test_ship_codex_groups_by_grade_not_rarity(self):
        game = AdventureGame(user_id="tester")
        game.start()

        ship = game._get_ship_by_id("comet_scout")
        self.assertIsNotNone(ship)
        self.assertEqual(ship.grade, "F")
        self.assertFalse(hasattr(ship, "rarity"))

        result = game._grant_ship_to_collection(ship)
        self.assertTrue(result["is_new"])
        self.assertEqual(result["count"], 1)

        duplicate = game._grant_ship_to_collection(ship)
        self.assertFalse(duplicate["is_new"])
        self.assertEqual(duplicate["count"], 2)

        # 도감 명령은 D1 메뉴, 목록이 실제 페이지
        menu = game.process_command("도감")
        self.assertIn("도감", menu)
        self.assertEqual(game.last_screen_id, "D1_CODEX")
        response = game.process_command("목록")
        self.assertIn("도감", response)
        self.assertIn("코멧 스카우트", response)
        self.assertIn("x2", response)
        self.assertIn("F ", response)
        # user-facing 구 희귀도 표기 제거
        for legacy in (
            "common",
            "rare",
            "epic",
            "legendary",
            "mythic",
            "⚪",
            "🔵",
            "🟣",
            "🟡",
            "🔴",
            " 일반",
            " 희귀",
            " 영웅",
            " 전설",
            " 신화",
        ):
            self.assertNotIn(legacy, response)

    def test_higher_grade_ship_inherits_body_enhance(self):
        game = AdventureGame(user_id="tester")
        game.start()
        game.ship_progress = game.ship_progress.with_body_enhance(100)
        game.ship_progress.equipped_ship_id = "comet_scout"
        game._sync_level_from_progress()

        higher = game._get_ship_by_id("ion_falcon")  # E
        self.assertIsNotNone(higher)
        self.assertEqual(higher.grade, "E")
        msg = game._maybe_equip_discovered_ship(higher)
        self.assertIsNotNone(msg)
        self.assertIn("계승", msg)
        self.assertEqual(game.ship_progress.grade.value, "E")
        self.assertEqual(game.ship_progress.body_enhance, 1)

    def test_first_equip_higher_grade_uses_inherit_enhance(self):
        """equipped_ship_id is None 이어도 상위 등급 첫 장착 시 등가 계승."""
        game = AdventureGame(user_id="tester")
        game.start()
        game.ship_progress = game.ship_progress.with_body_enhance(100)
        self.assertIsNone(game.ship_progress.equipped_ship_id)

        higher = game._get_ship_by_id("ion_falcon")  # E
        msg = game._maybe_equip_discovered_ship(higher)
        self.assertIsNotNone(msg)
        self.assertIn("계승", msg)
        self.assertEqual(game.ship_progress.grade.value, "E")
        self.assertEqual(game.ship_progress.body_enhance, 1)
        self.assertEqual(game.ship_progress.equipped_ship_id, "ion_falcon")

    def test_equivalent_power_preserves_success_rate_and_reward_scale(self):
        """F+100 과 E+1 의 성공률·보상 배율이 동일해야 한다 (등가 계승)."""
        from games.ship_system import ShipGrade, ShipProgress

        game = AdventureGame(user_id="tester")
        game.start()
        activity = game._get_activity_type("탐사")
        self.assertIsNotNone(activity)

        game.ship_progress = ShipProgress(grade=ShipGrade.F, body_enhance=100)
        game._sync_level_from_progress()
        rate_f = game._calculate_success_rate(activity)
        power_f = game._effective_power()
        with patch("games.adventure.random.random", return_value=0.5), patch(
            "games.adventure.random.randint", return_value=100
        ):
            # peak roll 비활성: 0.5 > 0.08
            reward_f = game._calculate_activity_reward(activity)

        game.ship_progress = ShipProgress(grade=ShipGrade.E, body_enhance=1)
        game._sync_level_from_progress()
        rate_e = game._calculate_success_rate(activity)
        power_e = game._effective_power()
        with patch("games.adventure.random.random", return_value=0.5), patch(
            "games.adventure.random.randint", return_value=100
        ):
            reward_e = game._calculate_activity_reward(activity)

        self.assertEqual(power_f, power_e)
        self.assertEqual(rate_f, rate_e)
        self.assertEqual(reward_f, reward_e)
        # raw body 를 쓰면 E+1 은 크게 떨어짐 — 등가 모델이면 98% 캡 근처
        self.assertGreaterEqual(rate_e, 98.0 - 0.01)

    def test_collection_without_equip_does_not_change_success_rate(self):
        game = AdventureGame(user_id="tester")
        game.start()
        activity = game._get_activity_type("정찰")
        self.assertIsNotNone(activity)

        game.ship_progress = game.ship_progress.with_body_enhance(0)
        base_rate = game._calculate_success_rate(activity)
        ship = game._get_ship_by_id("event_horizon")
        self.assertIsNotNone(ship)
        game._grant_ship_to_collection(ship)
        # 도감 수집 자체는 성공률에 영향 없음 (장착·계승 전)
        self.assertEqual(game._calculate_success_rate(activity), base_rate)

    def test_catalog_has_only_fs_grades_no_rarity_field(self):
        game = AdventureGame(user_id="tester")
        valid = {"F", "E", "D", "C", "B", "A", "S"}
        for ship in game.ship_catalog:
            self.assertIn(ship.grade, valid)
            self.assertFalse(hasattr(ship, "rarity"))
        # 이슈 매핑 스모크
        self.assertEqual(game._get_ship_by_id("lunar_moth").grade, "F")
        self.assertEqual(game._get_ship_by_id("quantum_fox").grade, "C")
        self.assertEqual(game._get_ship_by_id("event_horizon").grade, "S")

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
            game.ship_progress = game.ship_progress.with_body_enhance(2)
            game._persist_ship_progress()
            point_system.set_gold("tester", 1_000)

            success_rate = game._calculate_success_rate()
            near_miss_roll = (success_rate + 1.0) / 100
            with patch("games.adventure.random.random", return_value=near_miss_roll):
                response = game._enhance()

            self.assertIn("아슬아슬", response)
            self.assertEqual(game.current_level, 2)
            self.assertEqual(game.ship_progress.body_enhance, 2)
            self.assertEqual(point_system.get_enhancement_level("tester"), 2)

    def test_close_success_gets_celebration_bonus(self):
        with tempfile.NamedTemporaryFile() as db_file:
            point_system = GoldSystem(db_file.name)
            game = AdventureGame(user_id="tester", point_system=point_system)
            game.start()
            point_system.set_gold("tester", 1_000)

            success_rate = game._calculate_success_rate()
            clutch_roll = (success_rate - 1.0) / 100
            with patch("games.adventure.random.random", return_value=clutch_roll):
                response = game._enhance()

            self.assertIn("플라즈마 오버드라이브", response)
            self.assertIn("보너스 +", response)
            self.assertEqual(game.current_level, 1)
            self.assertEqual(game.ship_progress.body_enhance, 1)
            # 성공 시 파츠 중 하나가 +1
            self.assertEqual(sum(game.ship_progress.parts.values()), 1)

    def test_closer_success_gets_better_celebration(self):
        game = AdventureGame(user_id="tester")
        game.start()

        success_rate = game._calculate_success_rate()
        best = game._get_enhancement_celebration(success_rate - 0.2, success_rate)
        normal = game._get_enhancement_celebration(success_rate - 2.5, success_rate)

        self.assertIsNotNone(best)
        self.assertIsNotNone(normal)
        self.assertEqual(best.name, "초신성 점화")
        self.assertGreater(best.gold_multiplier, normal.gold_multiplier)

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
