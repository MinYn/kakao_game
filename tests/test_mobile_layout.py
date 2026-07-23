"""모바일 온리 응답 (이슈 #17) 레이아웃·depth 테스트."""

import unittest
from unittest.mock import patch

from games.adventure import AdventureGame
from ui.mobile_reply import (
    BUTTONS_DETAIL,
    BUTTONS_MENU,
    LayoutMode,
    MAX_LINE_CHARS,
    MAX_LINES_DETAIL,
    MAX_LINES_MENU,
    MobileReplyBuilder,
    fit_text,
    normalize_buttons,
    validate_reply,
    wrap_line,
)
from ui.screens import (
    D0_HOME,
    D1_GROW,
    D2_ENHANCE_RESULT,
    D2_MISSION_RESULT,
    get_registry,
    resolve_screen_for_command,
)


class FitTextTestCase(unittest.TestCase):
    def test_wrap_line_hard_cut(self):
        long = "가" * 40
        parts = wrap_line(long, 25)
        self.assertTrue(all(len(p) <= 25 for p in parts))
        self.assertEqual("".join(parts), long)

    def test_fit_text_limits_lines_and_chars(self):
        text = "\n".join(f"라인{i} " + ("X" * 30) for i in range(20))
        fitted = fit_text(text, max_lines=5, max_chars=25)
        lines = fitted.split("\n")
        self.assertLessEqual(len(lines), 5)
        for line in lines:
            self.assertLessEqual(len(line), 25)

    def test_no_blank_padding(self):
        fitted = fit_text("한줄만", max_lines=15)
        self.assertEqual(fitted, "한줄만")
        self.assertNotIn("\n\n", fitted)


class ScreenRegistryTestCase(unittest.TestCase):
    def test_depth_graph_valid(self):
        errors = get_registry().validate_depth_graph()
        self.assertEqual(errors, [], msg=errors)

    def test_menu_has_4_detail_has_2(self):
        for screen in get_registry().all_screens():
            if screen.layout is LayoutMode.MENU:
                self.assertEqual(len(screen.buttons), BUTTONS_MENU, screen.screen_id)
            else:
                self.assertEqual(len(screen.buttons), BUTTONS_DETAIL, screen.screen_id)

    def test_detail_has_home(self):
        for screen in get_registry().all_screens():
            if screen.layout is LayoutMode.DETAIL:
                messages = {b.message_text for b in screen.buttons}
                self.assertIn("홈", messages, screen.screen_id)

    def test_depth_max_3(self):
        for screen in get_registry().all_screens():
            self.assertGreaterEqual(screen.depth, 0)
            self.assertLessEqual(screen.depth, 3)

    def test_resolve_commands(self):
        self.assertEqual(resolve_screen_for_command("홈").screen_id, "D0_HOME")
        self.assertEqual(resolve_screen_for_command("성장").screen_id, "D1_GROW")
        self.assertEqual(resolve_screen_for_command("강화").screen_id, "D2_ENHANCE_RESULT")
        self.assertEqual(resolve_screen_for_command("출동").screen_id, "D2_MISSION_RESULT")
        self.assertEqual(resolve_screen_for_command("unknown-xyz").screen_id, "D0_HOME")


class MobileReplyBuilderTestCase(unittest.TestCase):
    def test_build_menu_and_detail(self):
        builder = MobileReplyBuilder()
        menu = builder.build_menu(
            ["홈", "라인2", "라인3", "라인4", "라인5", "잘림"],
            D0_HOME.button_dicts(),
            screen_id=D0_HOME.screen_id,
            depth=0,
        )
        self.assertEqual(menu.layout, LayoutMode.MENU)
        self.assertLessEqual(len(menu.text.split("\n")), MAX_LINES_MENU)
        self.assertEqual(len(menu.buttons), BUTTONS_MENU)
        self.assertEqual(validate_reply(menu), [])

        detail = builder.build_detail(
            ["결과"] + [f"L{i}" for i in range(20)],
            D2_ENHANCE_RESULT.button_dicts(),
            screen_id=D2_ENHANCE_RESULT.screen_id,
            depth=2,
        )
        self.assertLessEqual(len(detail.text.split("\n")), MAX_LINES_DETAIL)
        self.assertEqual(len(detail.buttons), BUTTONS_DETAIL)
        self.assertEqual(validate_reply(detail), [])

    def test_normalize_buttons_pads_and_trims(self):
        two = normalize_buttons([{"label": "A", "messageText": "a"}], LayoutMode.DETAIL)
        self.assertEqual(len(two), 2)
        four = normalize_buttons(
            [{"label": f"B{i}", "messageText": str(i)} for i in range(6)],
            LayoutMode.MENU,
        )
        self.assertEqual(len(four), 4)


class AdventureMobileFlowTestCase(unittest.TestCase):
    def test_start_is_d0_menu(self):
        game = AdventureGame(user_id="mobile-user")
        text = game.start()
        self.assertEqual(game.last_screen_id, "D0_HOME")
        lines = text.split("\n")
        self.assertLessEqual(len(lines), MAX_LINES_MENU)
        for line in lines:
            self.assertLessEqual(len(line), MAX_LINE_CHARS)
        buttons = game.get_command_buttons()
        self.assertEqual(len(buttons), 4)
        messages = [b["messageText"] for b in buttons]
        self.assertEqual(messages, ["성장", "출동", "도감", "상태"])

    def test_grow_menu_then_enhance_buttons(self):
        game = AdventureGame(user_id="mobile-user")
        game.start()
        text = game.process_command("성장")
        self.assertEqual(game.last_screen_id, "D1_GROW")
        self.assertIn("성장", text)
        buttons = game.get_command_buttons()
        self.assertEqual(len(buttons), 4)
        self.assertEqual([b["messageText"] for b in buttons], ["강화", "판매", "상세", "홈"])

    def test_mission_result_is_detail_with_2_buttons(self):
        game = AdventureGame(user_id="mobile-user")
        game.start()
        scout = game._get_activity_type("정찰")
        with patch.object(game, "_select_random_activity", return_value=scout), patch(
            "games.adventure.random.random", return_value=0.0
        ):
            text = game.process_command("출동")
        self.assertEqual(game.last_screen_id, "D2_MISSION_RESULT")
        self.assertIn("정찰 성공", text)
        lines = text.split("\n")
        self.assertLessEqual(len(lines), MAX_LINES_DETAIL)
        for line in lines:
            self.assertLessEqual(len(line), MAX_LINE_CHARS)
        buttons = game.get_command_buttons()
        self.assertEqual(len(buttons), 2)
        self.assertEqual(buttons[1]["messageText"], "홈")

    def test_unknown_command_returns_home(self):
        game = AdventureGame(user_id="mobile-user")
        game.start()
        text = game.process_command("이상한명령어xyz")
        self.assertEqual(game.last_screen_id, "D0_HOME")
        self.assertIn("홈", text)

    def test_home_escape_from_detail(self):
        game = AdventureGame(user_id="mobile-user")
        game.start()
        game.process_command("상세")
        self.assertEqual(game.last_screen_id, "D2_STATUS_DETAIL")
        game.process_command("홈")
        self.assertEqual(game.last_screen_id, "D0_HOME")

    def test_codex_pagination_stays_within_depth(self):
        game = AdventureGame(user_id="mobile-user")
        game.start()
        game.process_command("목록")
        self.assertIn(game.last_screen_id, ("D2_CODEX_PAGE", "D3_CODEX_PAGE"))
        depth = get_registry().require(game.last_screen_id).depth
        self.assertLessEqual(depth, 3)
        game.process_command("다음")
        depth2 = get_registry().require(game.last_screen_id).depth
        self.assertLessEqual(depth2, 3)
        text = game._last_reply.text if game._last_reply else ""
        for line in text.split("\n"):
            self.assertLessEqual(len(line), MAX_LINE_CHARS)

    def test_all_action_responses_obey_layout(self):
        game = AdventureGame(user_id="mobile-user")
        game.start()
        commands = ["성장", "상태", "도감", "패스", "상세", "목록", "홈"]
        for cmd in commands:
            game.process_command(cmd)
            reply = game._last_reply
            self.assertIsNotNone(reply)
            errors = validate_reply(reply)
            self.assertEqual(errors, [], msg=f"{cmd}: {errors} text={reply.text!r}")


if __name__ == "__main__":
    unittest.main()
