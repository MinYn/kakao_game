from __future__ import annotations

import hashlib
import random

from games.ship_system import body_enhance_to_upgrade_stage, parse_grade
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
    def upgrade_stage_from_body_enhance(body_enhance: int) -> int:
        """본체 +N → 배지 디테일 단계(0~3)."""
        return body_enhance_to_upgrade_stage(body_enhance)

    @staticmethod
    def upgrade_stage_from_attempts(attempts: int) -> int:
        """Deprecated: attempts 기반 단계. 본체 +N 매핑으로 대체.

        하위 호환을 위해 유지하되, 호출부는 body_enhance 경로를 쓰도록 한다.
        """
        attempts = max(0, attempts)
        # 대략 과거 임계값(5/10/20)을 body_enhance 밴드(5/15/30)에 가깝게 유지
        return body_enhance_to_upgrade_stage(attempts)

    @staticmethod
    def normalize_grade(grade: str | None) -> str:
        return parse_grade(grade).value

    @staticmethod
    def stable_seed(value: str) -> int:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return int(digest[:16], 16)
