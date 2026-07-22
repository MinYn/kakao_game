"""
기체 등급(F~S) · 본체 +N강 · 파츠 +N강 · 승급 계승 도메인.

이슈 #15 한 줄 모델:
  기체 = { name, grade: F~S, body_enhance: +0~N, shape, ... }
  파츠[] = { id, passive, part_enhance: +0~N }  # 파츠에 grade 없음

등가 앵커: F+100강 ≈ E+1강 (연속 등급마다 동일 곡선)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class ShipGrade(str, Enum):
    """기체 자체 등급 (파츠 등급이 아님). SS/S+는 범위 밖."""

    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"


GRADE_ORDER: tuple[ShipGrade, ...] = (
    ShipGrade.F,
    ShipGrade.E,
    ShipGrade.D,
    ShipGrade.C,
    ShipGrade.B,
    ShipGrade.A,
    ShipGrade.S,
)

GRADE_TONES: dict[ShipGrade, str] = {
    ShipGrade.F: "입문 기체",
    ShipGrade.E: "초기",
    ShipGrade.D: "초급 실전",
    ShipGrade.C: "중급",
    ShipGrade.B: "상급",
    ShipGrade.A: "정예",
    ShipGrade.S: "최고 티어",
}

# 도감 드롭 가중치 (F 흔함 → S 희귀). 기존 common~mythic 60/25/10/4/1 감을 7단계로 재분배.
GRADE_DROP_WEIGHTS: dict[ShipGrade, int] = {
    ShipGrade.F: 40,
    ShipGrade.E: 25,
    ShipGrade.D: 15,
    ShipGrade.C: 10,
    ShipGrade.B: 6,
    ShipGrade.A: 3,
    ShipGrade.S: 1,
}

# 레거시 희귀도 키 → 기체 등급 (저장 데이터/구 카탈로그 마이그레이션용)
LEGACY_RARITY_TO_GRADE: dict[str, ShipGrade] = {
    "common": ShipGrade.F,
    "rare": ShipGrade.E,
    "epic": ShipGrade.C,
    "legendary": ShipGrade.A,
    "mythic": ShipGrade.S,
    "일반": ShipGrade.F,
    "희귀": ShipGrade.E,
    "영웅": ShipGrade.C,
    "전설": ShipGrade.A,
    "신화": ShipGrade.S,
}


def grade_drop_weight(grade: str | ShipGrade) -> int:
    return GRADE_DROP_WEIGHTS[parse_grade(grade)]


def migrate_legacy_rarity(rarity: str | None) -> ShipGrade:
    """common/rare/… 또는 한글 희귀도 → F~S. 미지 값은 F."""
    if rarity is None or str(rarity).strip() == "":
        return ShipGrade.F
    key = str(rarity).strip().lower()
    if key in LEGACY_RARITY_TO_GRADE:
        return LEGACY_RARITY_TO_GRADE[key]
    # 이미 grade 문자인 경우
    try:
        return parse_grade(rarity)
    except ValueError:
        return ShipGrade.F

# 연속 등급 등가: G_i + (STEP+1) ≈ G_{i+1} + 1  →  F+100 ≈ E+1
LEVELS_PER_GRADE_STEP = 99

# 주요 스탯 키 (기체 +N / 등급 base에 공통 적용)
STAT_POWER = "power"
STAT_EFFICIENCY = "efficiency"
STAT_DURABILITY = "durability"
PRIMARY_STATS: tuple[str, ...] = (STAT_POWER, STAT_EFFICIENCY, STAT_DURABILITY)


def parse_grade(value: str | ShipGrade | None) -> ShipGrade:
    if isinstance(value, ShipGrade):
        return value
    if value is None or str(value).strip() == "":
        return ShipGrade.F
    key = str(value).strip().upper()
    try:
        return ShipGrade(key)
    except ValueError as exc:
        raise ValueError(f"unknown ship grade: {value!r}") from exc


def grade_index(grade: str | ShipGrade) -> int:
    g = parse_grade(grade)
    return GRADE_ORDER.index(g)


def grade_rank(grade: str | ShipGrade) -> int:
    """비교용 순위 (F=0 … S=6)."""
    return grade_index(grade)


def is_higher_grade(candidate: str | ShipGrade, current: str | ShipGrade) -> bool:
    return grade_rank(candidate) > grade_rank(current)


def base_stat(grade: str | ShipGrade) -> float:
    """등급 기본 스탯. base(S) > … > base(F)."""
    return float(grade_index(grade) * LEVELS_PER_GRADE_STEP)


def per_level(grade: str | ShipGrade) -> float:
    """등급별 강화 1강당 스탯 증가량.

    현재는 전 등급 동일(1.0). 밸런스 조정 시 계수만 바꾸면 되고,
    등가 앵커 F+100≈E+1 은 LEVELS_PER_GRADE_STEP 과 함께 테스트로 고정한다.
    """
    _ = parse_grade(grade)
    return 1.0


def stat(grade: str | ShipGrade, enhance_level: int) -> float:
    """주요 스탯 합(단일 축 등가). stat ≈ base(grade) + enhance * per_level(grade)."""
    enhance = max(0, int(enhance_level))
    return base_stat(grade) + enhance * per_level(grade)


def primary_stats(grade: str | ShipGrade, enhance_level: int) -> dict[str, float]:
    """주요 스탯 목록. 동일 곡선에 축별 배율을 적용한다."""
    core = stat(grade, enhance_level)
    return {
        STAT_POWER: core,
        STAT_EFFICIENCY: core * 0.95,
        STAT_DURABILITY: core * 1.05,
    }


def inherit_enhance(
    from_grade: str | ShipGrade,
    from_enhance: int,
    to_grade: str | ShipGrade,
) -> int:
    """상위/하위 등급 기체 교체 시 +N 환산.

    - 동급: +N 유지
    - 이종 등급: 이전 스탯 합을 보존하도록 N_to 계산 (반올림, 최소 0)
    - 예: F+100 → E+1
    """
    src = parse_grade(from_grade)
    dst = parse_grade(to_grade)
    n_from = max(0, int(from_enhance))
    if src == dst:
        return n_from

    preserved = stat(src, n_from)
    raw = (preserved - base_stat(dst)) / per_level(dst)
    return max(0, int(round(raw)))


def inherit_with_stats(
    from_grade: str | ShipGrade,
    from_enhance: int,
    to_grade: str | ShipGrade,
) -> tuple[int, float, float]:
    """계승 결과와 환산 전후 스탯을 함께 반환 (테스트/로그용)."""
    n_to = inherit_enhance(from_grade, from_enhance, to_grade)
    return n_to, stat(from_grade, from_enhance), stat(to_grade, n_to)


@dataclass(frozen=True)
class PartDefinition:
    """파츠 정의. 등급(F~S) 없음 — 패시브 + 강화(+N)만."""

    part_id: str
    name: str
    passive_label: str
    # 1강당 패시브 수치 (단위는 파츠별 해석)
    passive_per_level: float
    unit: str = "%"


PART_CATALOG: dict[str, PartDefinition] = {
    "engine": PartDefinition(
        part_id="engine",
        name="주 엔진",
        passive_label="탐사 보상",
        passive_per_level=1.0,
        unit="%",
    ),
    "sensor": PartDefinition(
        part_id="sensor",
        name="센서",
        passive_label="정찰 성공률",
        passive_per_level=0.3,
        unit="%p",
    ),
    "armor": PartDefinition(
        part_id="armor",
        name="장갑",
        passive_label="실패 페널티 감소",
        passive_per_level=0.5,
        unit="%p",
    ),
}

DEFAULT_PART_IDS: tuple[str, ...] = ("engine", "sensor", "armor")


@dataclass
class PartProgress:
    part_id: str
    enhance: int = 0

    def passive_value(self) -> float:
        definition = PART_CATALOG[self.part_id]
        return max(0, int(self.enhance)) * definition.passive_per_level

    def format_line(self) -> str:
        definition = PART_CATALOG[self.part_id]
        value = self.passive_value()
        return (
            f"{definition.name} +{max(0, int(self.enhance))}강 "
            f"({definition.passive_label} +{value:g}{definition.unit})"
        )


@dataclass
class ShipProgress:
    """유저 활성 기체 진행 상태."""

    grade: ShipGrade = ShipGrade.F
    body_enhance: int = 0
    equipped_ship_id: str | None = None
    parts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.grade = parse_grade(self.grade)
        self.body_enhance = max(0, int(self.body_enhance))
        normalized: dict[str, int] = {}
        for part_id in DEFAULT_PART_IDS:
            raw = self.parts.get(part_id, 0) if self.parts else 0
            normalized[part_id] = max(0, int(raw))
        # 알 수 없는 파츠 키는 무시 (등급 라벨 방지)
        self.parts = normalized

    @property
    def level(self) -> int:
        """하위 호환: 기존 enhancement level == 기체 body_enhance."""
        return self.body_enhance

    def part(self, part_id: str) -> PartProgress:
        return PartProgress(part_id=part_id, enhance=self.parts.get(part_id, 0))

    def part_list(self) -> list[PartProgress]:
        return [self.part(part_id) for part_id in DEFAULT_PART_IDS]

    def core_stat(self) -> float:
        return stat(self.grade, self.body_enhance)

    def primary_stats(self) -> dict[str, float]:
        return primary_stats(self.grade, self.body_enhance)

    def format_title(self, ship_name: str | None = None) -> str:
        name = ship_name or "미장착 기체"
        return f"{name} ★{self.grade.value}  +{self.body_enhance}강"

    def format_parts_summary(self) -> str:
        bits = []
        for part_id in DEFAULT_PART_IDS:
            definition = PART_CATALOG[part_id]
            bits.append(f"{definition.name} +{self.parts[part_id]}강")
        return ", ".join(bits)

    def format_status_block(self, ship_name: str | None = None) -> list[str]:
        stats = self.primary_stats()
        lines = [
            f"기체: {self.format_title(ship_name)}",
            f"- 등급 톤: {GRADE_TONES[self.grade]}",
            f"- 주 스탯 파워/효율/내구: "
            f"{stats[STAT_POWER]:.0f} / {stats[STAT_EFFICIENCY]:.0f} / {stats[STAT_DURABILITY]:.0f}",
            f"- 파츠: {self.format_parts_summary()}",
        ]
        for part in self.part_list():
            lines.append(f"  · {part.format_line()}")
        return lines

    def with_body_enhance(self, enhance: int) -> "ShipProgress":
        return ShipProgress(
            grade=self.grade,
            body_enhance=max(0, int(enhance)),
            equipped_ship_id=self.equipped_ship_id,
            parts=dict(self.parts),
        )

    def with_part_enhance(self, part_id: str, enhance: int) -> "ShipProgress":
        if part_id not in PART_CATALOG:
            raise ValueError(f"unknown part: {part_id}")
        parts = dict(self.parts)
        parts[part_id] = max(0, int(enhance))
        return ShipProgress(
            grade=self.grade,
            body_enhance=self.body_enhance,
            equipped_ship_id=self.equipped_ship_id,
            parts=parts,
        )

    def equip_ship(
        self,
        ship_id: str,
        new_grade: str | ShipGrade,
        *,
        inherit: bool = True,
    ) -> tuple["ShipProgress", int]:
        """기체 교체. 상위/이종 등급이면 본체 +N 계승. 파츠 +N은 유지."""
        dst = parse_grade(new_grade)
        if inherit:
            new_body = inherit_enhance(self.grade, self.body_enhance, dst)
        else:
            new_body = 0
        next_progress = ShipProgress(
            grade=dst,
            body_enhance=new_body,
            equipped_ship_id=ship_id,
            parts=dict(self.parts),
        )
        return next_progress, new_body

    def to_record(self) -> dict:
        return {
            "ship_grade": self.grade.value,
            "body_enhance": self.body_enhance,
            "level": self.body_enhance,
            "equipped_ship_id": self.equipped_ship_id,
            "part_engine": self.parts.get("engine", 0),
            "part_sensor": self.parts.get("sensor", 0),
            "part_armor": self.parts.get("armor", 0),
        }

    @classmethod
    def from_record(
        cls,
        record: Mapping | None,
        *,
        legacy_level_fallback: bool = True,
    ) -> "ShipProgress":
        if not record:
            return cls()
        # 마이그레이션:
        # - body_enhance 컬럼 없음 → level
        # - 복구/레거시 입력은 body_enhance=0 이고 level>0 일 때 level 사용
        # - 마이그레이션이 보장된 DB 저장소는 fallback=False 로 body 를 권위 값으로 사용
        raw_body = record.get("body_enhance")
        raw_level = record.get("level")
        level_val = int(raw_level or 0) if raw_level is not None else 0
        if raw_body is None:
            body = level_val
        else:
            body = int(raw_body or 0)
            if legacy_level_fallback and body == 0 and level_val > 0:
                body = level_val
        parts = {
            "engine": int(record.get("part_engine", 0) or 0),
            "sensor": int(record.get("part_sensor", 0) or 0),
            "armor": int(record.get("part_armor", 0) or 0),
        }
        return cls(
            grade=parse_grade(record.get("ship_grade") or record.get("grade") or "F"),
            body_enhance=max(0, body),
            equipped_ship_id=record.get("equipped_ship_id") or None,
            parts=parts,
        )


def migrate_legacy_level(level: int) -> ShipProgress:
    """기존 enhancement_levels.level → 기본 기체 grade F + body_enhance=level."""
    return ShipProgress(grade=ShipGrade.F, body_enhance=max(0, int(level)))


def body_enhance_to_upgrade_stage(body_enhance: int) -> int:
    """배지 비주얼 단계(0~3). upgrade_stage_from_attempts 대체."""
    enhance = max(0, int(body_enhance))
    if enhance >= 30:
        return 3
    if enhance >= 15:
        return 2
    if enhance >= 5:
        return 1
    return 0


def grade_to_visual_tier(grade: str | ShipGrade) -> int:
    """등급 → 실루엣/장식 티어(0~6)."""
    return grade_index(grade)


def format_grade_mark(grade: str | ShipGrade) -> str:
    return f"★{parse_grade(grade).value}"


def equivalence_table(
    pairs: Iterable[tuple[str | ShipGrade, int, str | ShipGrade]] | None = None,
) -> list[dict]:
    """등가표 fixture 생성 (문서/테스트용)."""
    if pairs is None:
        pairs = [
            (ShipGrade.F, 100, ShipGrade.E),
            (ShipGrade.E, 100, ShipGrade.D),
            (ShipGrade.D, 100, ShipGrade.C),
            (ShipGrade.C, 100, ShipGrade.B),
            (ShipGrade.B, 100, ShipGrade.A),
            (ShipGrade.A, 100, ShipGrade.S),
        ]
    rows = []
    for from_g, from_n, to_g in pairs:
        n_to, s_from, s_to = inherit_with_stats(from_g, from_n, to_g)
        rows.append(
            {
                "from": f"{parse_grade(from_g).value}+{from_n}",
                "to": f"{parse_grade(to_g).value}+{n_to}",
                "stat_from": s_from,
                "stat_to": s_to,
                "delta": abs(s_from - s_to),
            }
        )
    return rows
