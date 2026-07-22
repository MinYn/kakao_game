import unittest

from space_badges.generator import enhance_text_style, generate_svg
from space_badges.registry import BadgeVariant, ShipShape


class SpaceBadgeGeneratorTestCase(unittest.TestCase):
    def test_grade_mark_is_inside_badge_not_corner_origin(self):
        variant = BadgeVariant("TEST", "+0", ShipShape.SHUTTLE, "white")
        svg = generate_svg(variant, 1, star_seed=1, grade="S", body_enhance=0)
        self.assertIn('id="grade_badge_1"', svg)
        # 좌하단 안쪽 배치 (기존 48,48 바깥 코너 아님)
        self.assertIn('x="86" y="348"', svg)
        self.assertNotIn('x="48" y="48"', svg)

    def test_name_is_horizontal_banner_not_textpath(self):
        variant = BadgeVariant("COMET", "+0", ShipShape.SHUTTLE, "white")
        svg = generate_svg(variant, 2, star_seed=2, grade="F", body_enhance=0)
        self.assertIn("COMET", svg)
        self.assertIn('id="name_badge_2"', svg)
        self.assertNotIn("textPath", svg)

    def test_shape_and_color_change_background(self):
        shuttle = generate_svg(
            BadgeVariant("A", "+0", ShipShape.SHUTTLE, "white"), 3, grade="F"
        )
        rocket = generate_svg(
            BadgeVariant("B", "+0", ShipShape.ROCKET, "gold"), 4, grade="F"
        )
        # 배경 그라데이션 stop 색이 달라야 함
        self.assertNotEqual(shuttle, rocket)
        self.assertIn("#7dd3fc", shuttle)  # white override on shuttle theme
        self.assertIn("#fbbf24", rocket)  # gold override

    def test_enhance_text_style_tiers(self):
        self.assertEqual(enhance_text_style(0)["plate"], "#94a3b8")
        self.assertEqual(enhance_text_style(5)["plate"], "#22d3ee")
        self.assertEqual(enhance_text_style(15)["plate"], "#fbbf24")
        self.assertTrue(enhance_text_style(30)["glow"])

    def test_enhance_plate_uses_body_enhance_label(self):
        variant = BadgeVariant("NOVA", "BEEP", ShipShape.ROCKET, "orange")
        svg = generate_svg(variant, 5, grade="S", body_enhance=30)
        self.assertIn(">+30<", svg)
        self.assertIn("#f472b6", svg)  # high-tier plate


if __name__ == "__main__":
    unittest.main()
