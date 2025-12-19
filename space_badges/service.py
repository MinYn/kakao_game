from __future__ import annotations

import hashlib
import random

from space_badges.registry import BadgeVariant, VARIANTS


class SpaceBadgeService:
    def __init__(self, variants: list[BadgeVariant] | None = None) -> None:
        self.variants = variants or VARIANTS

    def get_variant_for_user(self, user_id: str, offset: int = 0) -> BadgeVariant:
        seed = self.stable_seed(f"{user_id}:{offset}")
        rng = random.Random(seed)
        return rng.choice(self.variants)

    def find_variant_index(self, variant: BadgeVariant) -> int:
        for index, candidate in enumerate(self.variants):
            if candidate == variant:
                return index
        return 0

    @staticmethod
    def upgrade_stage_from_level(level: int) -> int:
        level = max(0, level)
        return min(level // 5, 3)

    @staticmethod
    def stable_seed(value: str) -> int:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return int(digest[:16], 16)
