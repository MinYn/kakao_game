import unittest

from space_badges.generator import enhance_text_style, generate_svg
from space_badges.registry import BadgeVariant, ShipShape


class SpaceBadgeGeneratorTestCase(unittest.TestCase):
    def test_grade_mark_is_inside_badge_not_corner_origin(self):
        variant = BadgeVariant("TEST", "+0", ShipShape.SHUTTLE, "white")
        svg = generate_svg(variant, 1, star_seed=1, grade="S", body_enhance=0)
        self.assertIn('id="grade_badge_1"', svg)
        # 좌하단 안쪽 젬 프레임 (바깥 코너 48,48 아님)
        self.assertIn('x="74" y="348"', svg)
        self.assertNotIn('x="48" y="48"', svg)
        self.assertIn(">S<", svg)

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
        self.assertEqual(enhance_text_style(0)["plate"], "#f1f5f9")
        self.assertEqual(enhance_text_style(5)["plate"], "#a5f3fc")
        self.assertEqual(enhance_text_style(15)["plate"], "#fde68a")
        self.assertTrue(enhance_text_style(30)["glow"])
        # 시인성: 큰 폰트, 글자 외곽선 없음
        self.assertGreaterEqual(int(enhance_text_style(0)["font_size"]), 28)
        self.assertEqual(int(enhance_text_style(0)["stroke_w"]), 0)

    def test_enhance_plate_uses_body_enhance_label(self):
        variant = BadgeVariant("NOVA", "BEEP", ShipShape.ROCKET, "orange")
        svg = generate_svg(variant, 5, grade="S", body_enhance=30)
        self.assertIn(">+30<", svg)
        self.assertIn("#fbcfe8", svg)  # high-tier plate
        self.assertGreaterEqual(int(enhance_text_style(30)["font_size"]), 34)
        # 숫자 자체에 두꺼운 외곽 스트로크 없음
        enhance = svg[svg.index('id="enhance_badge_5"') :]
        enhance = enhance[: enhance.index("</g>") + 4]
        self.assertNotIn("stroke=", enhance[enhance.index("<text") :])

    def test_generate_svg_requires_explicit_grade_for_non_f(self):
        """HTTP 경로처럼 grade 를 넘기지 않으면 F 마크 — 호출부가 등급을 넘겨야 함."""
        variant = BadgeVariant("API", "+0", ShipShape.SHUTTLE, "white")
        default_svg = generate_svg(variant, 10, star_seed=1)
        graded_svg = generate_svg(variant, 11, star_seed=1, grade="S", body_enhance=12)
        self.assertIn(">F<", default_svg)
        self.assertIn(">S<", graded_svg)
        self.assertIn(">+12<", graded_svg)


if __name__ == "__main__":
    unittest.main()
