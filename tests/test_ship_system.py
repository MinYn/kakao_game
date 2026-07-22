import unittest

from games.ship_system import (
    GRADE_DROP_WEIGHTS,
    LEVELS_PER_GRADE_STEP,
    PART_CATALOG,
    ShipGrade,
    ShipProgress,
    body_enhance_to_upgrade_stage,
    equivalence_table,
    inherit_enhance,
    migrate_legacy_level,
    migrate_legacy_rarity,
    primary_stats,
    stat,
)


class ShipSystemTestCase(unittest.TestCase):
    def test_anchor_f100_equals_e1(self):
        self.assertEqual(inherit_enhance(ShipGrade.F, 100, ShipGrade.E), 1)
        self.assertAlmostEqual(stat(ShipGrade.F, 100), stat(ShipGrade.E, 1))

    def test_consecutive_grade_anchors(self):
        chain = [
            (ShipGrade.F, ShipGrade.E),
            (ShipGrade.E, ShipGrade.D),
            (ShipGrade.D, ShipGrade.C),
            (ShipGrade.C, ShipGrade.B),
            (ShipGrade.B, ShipGrade.A),
            (ShipGrade.A, ShipGrade.S),
        ]
        for lower, higher in chain:
            n_to = inherit_enhance(lower, LEVELS_PER_GRADE_STEP + 1, higher)
            self.assertEqual(n_to, 1, msg=f"{lower.value}+{LEVELS_PER_GRADE_STEP + 1} → {higher.value}")
            self.assertAlmostEqual(
                stat(lower, LEVELS_PER_GRADE_STEP + 1),
                stat(higher, 1),
                msg=f"stat mismatch {lower.value}→{higher.value}",
            )

    def test_same_grade_keeps_enhance(self):
        self.assertEqual(inherit_enhance(ShipGrade.C, 12, ShipGrade.C), 12)

    def test_downward_conversion(self):
        # E+1 → F 는 스탯 등가로 F+100
        self.assertEqual(inherit_enhance(ShipGrade.E, 1, ShipGrade.F), 100)

    def test_equivalence_table_zero_delta(self):
        for row in equivalence_table():
            self.assertEqual(row["delta"], 0.0)
            self.assertTrue(row["to"].endswith("+1"))

    def test_primary_stats_increase_with_grade_and_enhance(self):
        low = primary_stats(ShipGrade.F, 0)
        mid = primary_stats(ShipGrade.F, 10)
        high = primary_stats(ShipGrade.S, 0)
        self.assertGreater(mid["power"], low["power"])
        self.assertGreater(high["power"], mid["power"])
        self.assertIn("efficiency", low)
        self.assertIn("durability", low)

    def test_parts_have_no_grade_only_passive_enhance(self):
        for part in PART_CATALOG.values():
            self.assertFalse(hasattr(part, "grade"))
            self.assertTrue(part.passive_label)
            self.assertGreater(part.passive_per_level, 0)

    def test_ship_progress_format_and_equip_inherit(self):
        progress = ShipProgress(grade=ShipGrade.F, body_enhance=100, parts={"engine": 5})
        self.assertIn("★F", progress.format_title("아르테미스호"))
        self.assertIn("+100강", progress.format_title("아르테미스호"))
        self.assertIn("주 엔진 +5강", progress.format_parts_summary())

        next_progress, n_to = progress.equip_ship("ion_falcon", ShipGrade.E)
        self.assertEqual(n_to, 1)
        self.assertEqual(next_progress.grade, ShipGrade.E)
        self.assertEqual(next_progress.body_enhance, 1)
        self.assertEqual(next_progress.parts["engine"], 5)
        self.assertEqual(next_progress.equipped_ship_id, "ion_falcon")

    def test_migrate_legacy_level(self):
        migrated = migrate_legacy_level(7)
        self.assertEqual(migrated.grade, ShipGrade.F)
        self.assertEqual(migrated.body_enhance, 7)

    def test_from_record_legacy_level_only(self):
        progress = ShipProgress.from_record({"level": 3})
        self.assertEqual(progress.grade, ShipGrade.F)
        self.assertEqual(progress.body_enhance, 3)
        self.assertEqual(progress.to_record()["level"], 3)

    def test_from_record_stale_body_zero_uses_level(self):
        """마이그레이션 후 level 만 갱신된 행 → body_enhance=0 이어도 level 반영."""
        progress = ShipProgress.from_record(
            {"level": 7, "body_enhance": 0, "ship_grade": "F"}
        )
        self.assertEqual(progress.body_enhance, 7)
        self.assertEqual(progress.grade, ShipGrade.F)

    def test_from_record_can_treat_body_as_authoritative_after_migration(self):
        progress = ShipProgress.from_record(
            {"level": 7, "body_enhance": 0, "ship_grade": "E"},
            legacy_level_fallback=False,
        )
        self.assertEqual(progress.body_enhance, 0)
        self.assertEqual(progress.grade, ShipGrade.E)

    def test_body_enhance_upgrade_stage_bands(self):
        self.assertEqual(body_enhance_to_upgrade_stage(0), 0)
        self.assertEqual(body_enhance_to_upgrade_stage(5), 1)
        self.assertEqual(body_enhance_to_upgrade_stage(15), 2)
        self.assertEqual(body_enhance_to_upgrade_stage(30), 3)

    def test_grade_drop_weights_cover_all_grades(self):
        self.assertEqual(set(GRADE_DROP_WEIGHTS.keys()), set(ShipGrade))
        self.assertGreater(GRADE_DROP_WEIGHTS[ShipGrade.F], GRADE_DROP_WEIGHTS[ShipGrade.S])

    def test_migrate_legacy_rarity_to_grade(self):
        self.assertEqual(migrate_legacy_rarity("common"), ShipGrade.F)
        self.assertEqual(migrate_legacy_rarity("rare"), ShipGrade.E)
        self.assertEqual(migrate_legacy_rarity("epic"), ShipGrade.C)
        self.assertEqual(migrate_legacy_rarity("legendary"), ShipGrade.A)
        self.assertEqual(migrate_legacy_rarity("mythic"), ShipGrade.S)
        self.assertEqual(migrate_legacy_rarity("B"), ShipGrade.B)


if __name__ == "__main__":
    unittest.main()
