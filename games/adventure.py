import hashlib
import random
from dataclasses import dataclass
from typing import Dict, Optional

from games.base_game import Game
from games.ship_system import (
    GRADE_DROP_WEIGHTS,
    GRADE_ORDER,
    GRADE_TONES,
    PART_CATALOG,
    ShipGrade,
    ShipProgress,
    body_enhance_to_upgrade_stage,
    format_grade_mark,
    is_higher_grade,
    parse_grade,
)
from config import Config


@dataclass
class ActivityType:
    """우주 임무 타입 정보"""

    name: str
    base_reward: int
    reward_range: tuple
    multiplier: float | None = None
    prompts: tuple[str, ...] = ()
    success_rate: float = 80.0
    success_messages: tuple[str, ...] = ()
    fail_messages: tuple[str, ...] = ()
    # 통합 출동 시 랜덤 선택 가중치 (높을수록 자주 등장)
    weight: int = 1
    icon: str = "🎯"


@dataclass(frozen=True)
class CollectibleShip:
    """도감에 등록되는 수집형 우주선.

    기체 티어는 grade(F~S) 만 사용한다.
    common/rare/epic/legendary/mythic 희귀도 필드는 없다.
    """

    ship_id: str
    name: str
    grade: str
    flavor: str

    @property
    def ship_grade(self) -> ShipGrade:
        return parse_grade(self.grade)


@dataclass(frozen=True)
class LootDrop:
    """임무 성공 후 즉시 보상되는 득템 테이블"""

    name: str
    icon: str
    chance: float
    gold_range: tuple[int, int]
    message: str


@dataclass(frozen=True)
class EnhancementCelebration:
    """강화 성공선에 가까울수록 커지는 축하 이펙트"""

    name: str
    icon: str
    max_margin: float
    gold_multiplier: float
    message: str


@dataclass
class ExplorerProfile:
    """사용자별 고유 탐사대 프로필 (로컬 결정적 생성)"""

    call_sign: str
    role: str
    ship_class: str
    module: str
    temperament: str
    badge: str

    @classmethod
    def from_user_id(cls, user_id: str) -> "ExplorerProfile":
        seed = int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed)

        roles = ["궤도 조종사", "심우주 정찰관", "행성 지질학자", "통신 기사", "구조 대원"]
        ships = ["탐사 셔틀", "정찰 프리깃", "과학 코르벳", "수송 드론", "지원 크루저"]
        modules = ["과학 모듈", "레이더 팩", "엔진 튠", "차폐 장치", "응급 키트"]
        temperaments = ["냉정한", "호기심 많은", "신속한", "분석적인", "대담한"]

        role = rng.choice(roles)
        ship_class = rng.choice(ships)
        module = rng.choice(modules)
        temperament = rng.choice(temperaments)
        call_sign = f"STS-{rng.randint(100, 999)}"

        badge_rng = random.Random(seed ^ 0xABCDEF)
        nose = badge_rng.choice(["/\\", "^", "Λ", "A", "Δ"])
        body = badge_rng.choice(["===>", "--->", "-==>", "~=>"])
        trail = badge_rng.choice(["⋆", "✦", "✧", ""],)
        badge = f"  {nose}\n{body}🚀{trail}\n  ||"

        return cls(
            call_sign=call_sign,
            role=role,
            ship_class=ship_class,
            module=module,
            temperament=temperament,
            badge=badge,
        )


class AdventureGame(Game):
    """우주 탐험 로그 게임"""

    def __init__(self, user_id: str, point_system=None):
        super().__init__(user_id, point_system)
        self.max_level = None  # 최대 레벨 제한 없음
        self.current_level = 0  # body_enhance 별칭 (하위 호환)
        self.ship_progress = ShipProgress()
        self.enhancement_cost_base = Config.ENHANCEMENT_BASE_COST
        self.enhancement_cost_multiplier = Config.ENHANCEMENT_COST_MULTIPLIER
        self.sell_multiplier = Config.ENHANCEMENT_SELL_MULTIPLIER
        self.level_bonus = Config.ENHANCEMENT_LEVEL_BONUS
        self.grade_drop_weights = dict(GRADE_DROP_WEIGHTS)
        self.ship_catalog = self._init_ship_catalog()
        self.loot_table = self._init_loot_table()
        self.enhancement_celebrations = self._init_enhancement_celebrations()

        self.activities = self._init_activities()
        self.activity_stats: Dict[str, int] = {a.name: 0 for a in self.activities}
        self.activity_count = 0
        self.total_reward = 0
        self.explorer_profile: Optional[ExplorerProfile] = None
        self.command_definitions = self._init_command_definitions()
        self._build_command_index()

    def _init_ship_catalog(self) -> list[CollectibleShip]:
        """우주선 도감 카탈로그. 티어는 grade(F~S)만 사용 (rarity 필드 없음).

        이슈 #15 매핑 초안:
          common→F, rare→E/D, epic→C/B, legendary→A, mythic→S
        """
        return [
            CollectibleShip("comet_scout", "코멧 스카우트", "F", "근거리 정찰에 최적화된 입문형 기체"),
            CollectibleShip("cargo_mule", "카고 뮬", "F", "잔해 지대에서 부품을 안정적으로 회수하는 수송선"),
            CollectibleShip("lunar_moth", "루나 모스", "F", "달빛 반사 도장으로 초보 조종사에게 인기"),
            CollectibleShip("ion_falcon", "아이온 팔콘", "E", "이온 항로를 빠르게 가로지르는 민첩한 프리깃"),
            CollectibleShip("nebula_ray", "네뷸라 레이", "D", "성운 속 신호 탐지에 강한 센서함"),
            CollectibleShip("aurora_clip", "오로라 클립", "D", "극광 입자를 연료로 쓰는 실험기"),
            CollectibleShip("quantum_fox", "퀀텀 폭스", "C", "짧은 양자 도약으로 위기 상황을 벗어나는 고급 기체"),
            CollectibleShip("void_manta", "보이드 만타", "B", "암흑 물질 표면 코팅을 두른 심우주 탐사선"),
            CollectibleShip("solar_dragon", "솔라 드래곤", "A", "항성풍을 타고 날아가는 정예 순양함"),
            CollectibleShip("event_horizon", "이벤트 호라이즌", "S", "블랙홀 경계에서 회수된 최고 티어 함선"),
        ]

    def _init_loot_table(self) -> list[LootDrop]:
        """임무 후 즉시 보상되는 득템 테이블. 경제 밸런스는 여기서만 조정."""
        return [
            LootDrop("고철 부품 상자", "📦", 0.12, (25, 60), "버려진 부품 상자를 회수했습니다."),
            LootDrop("희귀 연료 셀", "💎", 0.045, (90, 180), "푸른빛 연료 셀이 스캐너에 잡혔습니다!"),
            LootDrop("고대 항법 코어", "🌌", 0.012, (300, 650), "고대 항법 코어가 깨어났습니다. 오늘 운이 미쳤어요!"),
        ]

    def _init_enhancement_celebrations(self) -> list[EnhancementCelebration]:
        """성공선에 가까울수록 더 큰 이펙트/보너스 제공"""
        return [
            EnhancementCelebration("초신성 점화", "🌠", 0.5, 0.50, "성공선 바로 위에서 코어가 폭발적으로 점화됐습니다!"),
            EnhancementCelebration("플라즈마 오버드라이브", "⚡", 1.5, 0.30, "거의 미끄러질 뻔한 순간 출력이 치솟았습니다!"),
            EnhancementCelebration("스파크 세리머니", "✨", 3.0, 0.15, "아슬아슬한 성공에 정비 드론들이 불꽃을 터뜨립니다!"),
        ]

    def _get_ship_by_id(self, ship_id: str) -> Optional[CollectibleShip]:
        return next((ship for ship in self.ship_catalog if ship.ship_id == ship_id), None)

    def _equipped_ship(self) -> Optional[CollectibleShip]:
        if self.ship_progress.equipped_ship_id:
            return self._get_ship_by_id(self.ship_progress.equipped_ship_id)
        return None

    def _equipped_ship_name(self) -> str:
        ship = self._equipped_ship()
        if ship:
            return ship.name
        if self.explorer_profile:
            return self.explorer_profile.ship_class
        return "기본 셔틀"

    def _sync_level_from_progress(self) -> None:
        self.current_level = self.ship_progress.body_enhance
        self.game_data["level"] = self.current_level
        self.game_data["ship_grade"] = self.ship_progress.grade.value
        self.game_data["body_enhance"] = self.ship_progress.body_enhance
        self.game_data["equipped_ship_id"] = self.ship_progress.equipped_ship_id
        self.game_data["parts"] = dict(self.ship_progress.parts)

    def _persist_ship_progress(self) -> None:
        self._sync_level_from_progress()
        if self.point_system and hasattr(self.point_system, "set_ship_progress"):
            self.point_system.set_ship_progress(self.user_id, self.ship_progress)
        elif self.point_system:
            self.point_system.set_enhancement_level(self.user_id, self.ship_progress.body_enhance)

    def _load_ship_progress(self) -> ShipProgress:
        if self.point_system and hasattr(self.point_system, "get_ship_progress"):
            return self.point_system.get_ship_progress(self.user_id)
        if self.point_system:
            level = self.point_system.get_enhancement_level(self.user_id)
            return ShipProgress(grade=ShipGrade.F, body_enhance=level)
        return ShipProgress()

    def _roll_collectible_ship(self) -> CollectibleShip:
        """grade 드롭 가중치 → 해당 등급 내 균등 선택."""
        grades = list(GRADE_ORDER)
        weights = [self.grade_drop_weights[g] for g in grades]
        selected_grade = random.choices(grades, weights=weights, k=1)[0]
        candidates = [
            ship for ship in self.ship_catalog if ship.ship_grade == selected_grade
        ]
        if not candidates:
            # 해당 등급 기체가 없으면 카탈로그 전체에서 균등
            return random.choice(self.ship_catalog)
        return random.choice(candidates)

    def _get_collection_records(self) -> dict[str, int]:
        if self.point_system and hasattr(self.point_system, "get_ship_collection"):
            records = self.point_system.get_ship_collection(self.user_id)
            return {record["ship_id"]: record.get("count", 1) for record in records}
        return self.game_data.setdefault("ship_collection", {})

    def _grant_ship_to_collection(self, ship: CollectibleShip) -> dict:
        if self.point_system and hasattr(self.point_system, "add_ship_to_collection"):
            return self.point_system.add_ship_to_collection(self.user_id, ship.ship_id)

        collection = self._get_collection_records()
        old_count = collection.get(ship.ship_id, 0)
        collection[ship.ship_id] = old_count + 1
        return {"ship_id": ship.ship_id, "is_new": old_count == 0, "count": collection[ship.ship_id]}

    def _maybe_equip_discovered_ship(self, ship: CollectibleShip) -> Optional[str]:
        """상위 등급 기체 발견 시 장착 + 본체 +N 등가 계승. 파츠 +N은 유지."""
        current = self.ship_progress
        if current.equipped_ship_id is None:
            self.ship_progress = ShipProgress(
                grade=ship.ship_grade,
                body_enhance=current.body_enhance,
                equipped_ship_id=ship.ship_id,
                parts=dict(current.parts),
            )
            self._persist_ship_progress()
            return (
                f"🛠️ 주력 기체 장착: {ship.name} {format_grade_mark(ship.grade)} "
                f"+{self.ship_progress.body_enhance}강"
            )

        if not is_higher_grade(ship.grade, current.grade):
            return None

        prev_title = current.format_title(self._equipped_ship_name())
        next_progress, new_n = current.equip_ship(ship.ship_id, ship.grade, inherit=True)
        self.ship_progress = next_progress
        self._persist_ship_progress()
        return (
            f"⬆️ 상위 등급 기체 계승!\n"
            f"  {prev_title}\n"
            f"  → {next_progress.format_title(ship.name)}\n"
            f"  (본체 +N 등가 환산, 파츠 강화 유지 · {GRADE_TONES[next_progress.grade]})"
        )

    def get_badge_upgrade_stage(self) -> int:
        """배지 디테일 단계: 본체 +N 기반 (attempts 기반 폐기)."""
        return body_enhance_to_upgrade_stage(self.ship_progress.body_enhance)

    def get_ship_grade_value(self) -> str:
        return self.ship_progress.grade.value

    def _init_activities(self) -> list:
        """활동 타입 초기화.

        정찰/탐사/구조는 통합 '출동' 커맨드에서 가중치 랜덤으로 결정된다.
        weight 합계 기준 대략: 정찰 50% / 탐사 35% / 구조 15% (패스 있을 때).
        """
        return [
            ActivityType(
                name="정찰",
                base_reward=30,
                reward_range=(20, 45),
                multiplier=0.08,
                prompts=("정찰", "scout", "walk", "n", "1"),
                success_rate=86.0,
                weight=50,
                icon="🛰️",
                success_messages=(
                    "{pilot}이(가) 저궤도 정찰을 마치고 안전하게 복귀했습니다.",
                    "{pilot} 콜사인이 남긴 센서 로그가 깔끔합니다!",
                    "{pilot}이(가) 잔해 지대를 스캔해 유용한 데이터를 확보했어요.",
                ),
                fail_messages=(
                    "태양 플레어가 강해 임무를 축소했습니다.",
                    "센서 노이즈가 커서 재시도가 필요합니다.",
                    "연료 절약을 위해 빠르게 회항했습니다.",
                ),
            ),
            ActivityType(
                name="탐사",
                base_reward=85,
                reward_range=(65, 125),
                multiplier=0.12,
                prompts=("탐사", "survey", "play", "s", "2"),
                success_rate=78.0,
                weight=35,
                icon="🧭",
                success_messages=(
                    "{pilot}이(가) 샘플 채취에 성공했습니다! 분석 크레딧 확보.",
                    "{pilot}이(가) 지질 코어를 회수하고 보고서를 남겼습니다.",
                    "{pilot}이(가) 외계 구조물을 기록해 연구 포인트를 얻었습니다.",
                ),
                fail_messages=(
                    "표본이 손상되어 다시 채취가 필요합니다.",
                    "드론이 전송을 끊어 임무를 중단했습니다.",
                    "기상 악화로 탐사를 연기했습니다.",
                ),
            ),
            ActivityType(
                name="구조",
                base_reward=210,
                reward_range=(170, 280),
                multiplier=0.17,
                prompts=("구조", "rescue", "challenge", "boss", "b", "3"),
                success_rate=64.0,
                weight=15,
                icon="🚨",
                success_messages=(
                    "{pilot}이(가) 조난 신호를 따라가 승선자를 무사히 구출했습니다!",
                    "{pilot} 팀이 위험 구역을 돌파해 화물을 회수했습니다!",
                    "{pilot}이(가) 침몰 직전의 캡슐을 견인했습니다. 대원들이 환호합니다!",
                ),
                fail_messages=(
                    "신호가 약해 경로를 잃었습니다. 다시 좌표를 보정합니다.",
                    "차폐가 부족해 접근이 좌절됐습니다. 업그레이드가 필요합니다.",
                    "연료가 부족해 안전히 철수했습니다.",
                ),
            ),
        ]

    def _init_command_definitions(self) -> list:
        """구조화된 커맨드/버튼 정의"""
        return [
            {
                "key": "enhance",
                "triggers": ["성장", "train", "강화", "업그레이드", "개조"],
                "handler": self._enhance,
                "button": {"label": "🔨 강화", "messageText": "강화"},
            },
            {
                "key": "sell",
                "triggers": ["정산", "sell", "추억", "돌아보기", "판매"],
                "handler": self._sell,
                "button": {"label": "💰 판매", "messageText": "판매"},
            },
            {
                "key": "status",
                "triggers": ["상태", "status", "info"],
                "handler": self._get_status,
                "button": {"label": "📊 상태", "messageText": "상태"},
            },
            {
                "key": "codex",
                "triggers": ["도감", "collection", "codex", "수집", "ships"],
                "handler": self._show_ship_codex,
                "button": {"label": "📚 도감", "messageText": "도감"},
            },
            {
                "key": "passes",
                "triggers": ["패스", "ticket", "tickets", "t"],
                "handler": self._show_passes,
                "button": {"label": "🎫 패스", "messageText": "패스"},
            },
            {
                # 정찰/탐사/구조를 단일 진입점으로 통합. 실행 시 이벤트 종류가 랜덤 결정됨.
                # 기존 개별 커맨드(정찰/탐사/구조 등)는 alias로 유지해 호환.
                "key": "mission",
                "triggers": [
                    "출동",
                    "mission",
                    "탐험",
                    "go",
                    "m",
                    "0",
                    # 기존 개별 커맨드 alias
                    "정찰",
                    "walk",
                    "scout",
                    "n",
                    "1",
                    "탐사",
                    "play",
                    "survey",
                    "s",
                    "2",
                    "특별놀이",
                    "구조",
                    "challenge",
                    "rescue",
                    "boss",
                    "b",
                    "3",
                ],
                "handler": self._perform_mission,
                "button": {"label": "🚀 출동", "messageText": "출동"},
            },
        ]

    def get_command_buttons(self, last_command: Optional[str] = None) -> list[dict]:
        """모험 게임용 버튼 우선순위 제공"""
        key_order = [
            "enhance",
            "mission",
            "codex",
            "sell",
            "status",
            "passes",
        ]

        definition_by_key = {d.get("key"): d for d in self.get_command_definitions()}
        buttons: list[dict] = []

        for key in key_order:
            definition = definition_by_key.get(key)
            if not definition or not definition.get("button"):
                continue

            button_meta = definition["button"]
            label = button_meta.get("label") or definition.get("label")
            message_text = button_meta.get("messageText") or next(
                iter(definition.get("triggers", [])),
                "",
            )

            if label and message_text:
                buttons.append({"label": label, "messageText": message_text})

        return buttons[:5]

    def _load_stats(self) -> Dict[str, int]:
        if self.point_system:
            stats = self.point_system.get_game_stats(self.user_id)
            progress = self._load_ship_progress()
            return {
                "level": progress.body_enhance,
                "ship_progress": progress,
                "activity_count": stats.get("total_hunts", 0),
                "total_reward": stats.get("total_hunt_reward", 0),
                "activity_stats": {
                    "정찰": stats.get("hunt_normal", 0),
                    "탐사": stats.get("hunt_special", 0),
                    "구조": stats.get("hunt_boss", 0),
                },
                "attempts": stats.get("enhancement_attempts", 0),
                "successes": stats.get("enhancement_successes", 0),
                "failures": stats.get("enhancement_failures", 0),
            }

        return {
            "level": 0,
            "ship_progress": ShipProgress(),
            "activity_count": 0,
            "total_reward": 0,
            "activity_stats": {"정찰": 0, "탐사": 0, "구조": 0},
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "badge_cycle": 0,
        }

    def start(self) -> str:
        """게임 시작"""
        self.is_active = True
        self.explorer_profile = ExplorerProfile.from_user_id(self.user_id)
        stats = self._load_stats()

        self.ship_progress = stats.get("ship_progress") or ShipProgress()
        self.current_level = self.ship_progress.body_enhance
        self.activity_count = stats["activity_count"]
        self.total_reward = stats["total_reward"]
        self.activity_stats = stats["activity_stats"].copy()
        self.game_data = {
            "level": self.current_level,
            "ship_grade": self.ship_progress.grade.value,
            "body_enhance": self.ship_progress.body_enhance,
            "equipped_ship_id": self.ship_progress.equipped_ship_id,
            "parts": dict(self.ship_progress.parts),
            "attempts": stats["attempts"],
            "successes": stats["successes"],
            "failures": stats["failures"],
            "activity_count": self.activity_count,
            "total_reward": self.total_reward,
            "activity_stats": self.activity_stats,
            "badge_cycle": stats.get("badge_cycle", 0),
        }

        challenge_passes = self._get_challenge_passes()
        ship_title = self.ship_progress.format_title(self._equipped_ship_name())
        pilot_card = (
            f"{self.explorer_profile.badge}\n"
            f"콜사인: {self.explorer_profile.call_sign}\n"
            f"역할: {self.explorer_profile.role}\n"
            f"기체: {ship_title}\n"
            f"모듈: {self.explorer_profile.module}\n"
            f"기질: {self.explorer_profile.temperament}"
        )

        return (
            "🛰️ 우주 탐험 로그를 시작합니다!\n\n"
            f"{pilot_card}\n\n"
            f"현재 우주선: {ship_title}\n"
            f"파츠: {self.ship_progress.format_parts_summary()}\n"
            f"우주선 도감: {len(self._get_collection_records())}/{len(self.ship_catalog)}종 수집\n"
            f"구조 임무 패스: {challenge_passes}장\n\n"
            "명령어:\n"
            "✨ 강화: '성장'/'train'/'강화'/'업그레이드' (본체 +N강, 골드 사용)\n"
            "💾 정산: '정산'/'sell' (본체 강화 초기화 후 보상)\n"
            "📊 상태보기: '상태'/'status'\n"
            "📚 도감보기: '도감'/'collection'\n\n"
            "🎯 활동:\n"
            "- '출동'/'mission': 랜덤 이벤트(정찰·탐사·구조) 임무 진행\n"
            "- '패스'/'ticket': 보유 구조 패스 확인\n"
            "💡 상위 등급 기체 발견 시 본체 +N이 등가 환산으로 계승됩니다.\n"
            "💡 기존 '정찰'/'탐사'/'구조' 입력도 출동으로 연결됩니다."
        )

    def process_command(self, command: str) -> str:
        """명령 처리"""
        start_message = None
        if not self.is_active:
            start_message = self.start()

        response, _ = self.run_structured_command(command)
        if response:
            return f"{start_message}\n\n{response}" if start_message else response

        fallback = (
            "알 수 없는 명령입니다.\n"
            "사용 가능한 명령: 성장, 정산, 출동, 패스, 상태, 도감"
        )
        if start_message:
            return f"{start_message}\n\n{fallback}"
        return fallback

    # ========== 성장 관련 메서드 ==========

    def _calculate_cost(self) -> int:
        """본체 +N 강화 비용 계산"""
        cost = int(
            self.enhancement_cost_base
            * (self.enhancement_cost_multiplier ** self.ship_progress.body_enhance)
        )
        return max(cost, 10)

    def _calculate_success_rate(self, activity: Optional[ActivityType] = None) -> float:
        """성공 확률 계산. 본체 +N + 센서 파츠 패시브."""
        base_rate = activity.success_rate if activity else 80.0
        body_boost = self.ship_progress.body_enhance * 2
        sensor_boost = self.ship_progress.part("sensor").passive_value()
        if activity and activity.name != "정찰":
            # 센서 패시브는 정찰에 더 크게, 그 외 활동은 절반 반영
            sensor_boost *= 0.5
        boosted = min(base_rate + body_boost + sensor_boost, 98.0)
        return max(boosted, 25.0)

    def _get_enhancement_celebration(
        self,
        roll: float,
        success_rate: float,
    ) -> Optional[EnhancementCelebration]:
        """성공선에 가까운 성공일수록 더 높은 축하 이펙트 반환"""
        margin = success_rate - roll
        if margin < 0:
            return None
        for celebration in self.enhancement_celebrations:
            if margin <= celebration.max_margin:
                return celebration
        return None

    def _is_enhancement_near_miss(self, roll: float, success_rate: float) -> bool:
        """실패 직후 5% 구간은 단계 하락을 막아 아슬아슬한 재미 제공"""
        return 0 < roll - success_rate <= 5.0

    def _calculate_sell_price(self) -> int:
        """정산 금액 계산"""
        if self.current_level == 0:
            return 0

        total_invested = 0
        for level in range(self.current_level):
            level_cost = int(
                self.enhancement_cost_base * (self.enhancement_cost_multiplier ** level)
            )
            total_invested += max(level_cost, 10)

        sell_price = int(total_invested * self.sell_multiplier)
        level_bonus_amount = self.current_level * self.level_bonus
        sell_price += level_bonus_amount

        if self.current_level >= 10:
            sell_price += int(sell_price * 0.2)
        elif self.current_level >= 5:
            sell_price += int(sell_price * 0.1)

        return max(sell_price, 10)

    def _enhance(self) -> str:
        """기체 본체 +N 강화 (파츠 등급 없음)."""
        cost = self._calculate_cost()
        before = self.ship_progress.body_enhance
        ship_title = self.ship_progress.format_title(self._equipped_ship_name())

        if not self.point_system or not self.point_system.has_gold(self.user_id, cost):
            return (
                "❌ 우주선 강화를 위한 골드가 부족합니다.\n"
                f"필요 골드: {cost}G\n현재 골드: {self.get_user_points()}G\n"
                f"대상: {ship_title}"
            )

        self.deduct_gold(cost, f"본체 강화 시도 ({ship_title} +{before} → +{before + 1})")

        self.game_data["attempts"] = self.game_data.get("attempts", 0) + 1
        if self.point_system:
            self.point_system.update_game_stats(user_id=self.user_id, enhancement_attempts=1)

        success_rate = self._calculate_success_rate()
        roll = random.random() * 100
        is_success = roll < success_rate

        if is_success:
            self.ship_progress = self.ship_progress.with_body_enhance(before + 1)
            # 성공 시 랜덤 파츠 +1 (패시브 성장)
            part_id = random.choice(list(PART_CATALOG.keys()))
            part_before = self.ship_progress.parts.get(part_id, 0)
            self.ship_progress = self.ship_progress.with_part_enhance(part_id, part_before + 1)
            self._persist_ship_progress()
            self.game_data["successes"] = self.game_data.get("successes", 0) + 1
            if self.point_system:
                self.point_system.update_game_stats(user_id=self.user_id, enhancement_successes=1)

            next_cost = self._calculate_cost()
            celebration = self._get_enhancement_celebration(roll, success_rate)
            celebration_lines: list[str] = []
            if celebration:
                bonus = max(int(cost * celebration.gold_multiplier), 10)
                self.award_gold(bonus, f"강화 축하 이펙트: {celebration.name}")
                celebration_lines = [
                    f"{celebration.icon} {celebration.name} 축하 이펙트!",
                    f"판정 차이 {success_rate - roll:.1f}%p — {celebration.message}",
                    f"보너스 +{bonus}G",
                    "",
                ]

            part_def = PART_CATALOG[part_id]
            result_lines = [
                "✅ 강화 성공!",
                "",
                f"기체: {self.ship_progress.format_title(self._equipped_ship_name())}",
                f"파츠 성장: {part_def.name} +{part_before + 1}강",
                f"다음 본체 강화 필요 골드: {next_cost}G",
                f"현재 골드: {self.get_user_points()}G",
                "",
            ]
            result_lines.extend(celebration_lines)
            result_lines.append(
                "💡 기체 등급(F~S) · 본체 +N · 파츠 +N 을 구분해 보세요. 파츠에는 등급이 없습니다."
            )
            return "\n".join(result_lines)

        self.game_data["failures"] = self.game_data.get("failures", 0) + 1
        if self.point_system:
            self.point_system.update_game_stats(user_id=self.user_id, enhancement_failures=1)

        armor_save = self.ship_progress.part("armor").passive_value()
        if self.ship_progress.body_enhance > 0 and (
            self._is_enhancement_near_miss(roll, success_rate)
            or (armor_save > 0 and random.random() * 100 < min(armor_save, 25))
        ):
            return (
                "🛡️ 아슬아슬하게 버텼습니다!\n\n"
                f"성공률 {success_rate:.1f}% / 판정 {roll:.1f}%\n"
                "보호막/장갑이 간신히 버텨 본체 강화가 내려가지 않았어요.\n"
                f"기체: {self.ship_progress.format_title(self._equipped_ship_name())}\n"
                f"현재 골드: {self.get_user_points()}G\n\n"
                "방금 거의 붙을 뻔했습니다. 한 번 더?"
            )

        if self.ship_progress.body_enhance > 0:
            self.ship_progress = self.ship_progress.with_body_enhance(
                self.ship_progress.body_enhance - 1
            )
            self._persist_ship_progress()
            return (
                "❌ 본체 강화가 한 단계 내려갔어요.\n\n"
                f"기체: {self.ship_progress.format_title(self._equipped_ship_name())}\n"
                f"현재 골드: {self.get_user_points()}G\n\n"
                "다시 시도해볼까요?"
            )

        return (
            "❌ 강화 실패...\n\n"
            f"기체: {self.ship_progress.format_title(self._equipped_ship_name())}\n"
            f"현재 골드: {self.get_user_points()}G\n\n"
            "다시 한 번 시도해보세요!"
        )

    def _sell(self) -> str:
        """본체 강화 정산 (등급/파츠/장착 기체는 유지)."""
        if self.ship_progress.body_enhance == 0:
            return "❌ 정산할 본체 강화가 없습니다. 강화 후 정산해 주세요."

        sell_price = self._calculate_sell_price()
        sold_level = self.ship_progress.body_enhance
        sold_title = self.ship_progress.format_title(self._equipped_ship_name())

        if self.point_system:
            self.award_gold(sell_price, f"본체 강화 정산 ({sold_title})")

        self.ship_progress = self.ship_progress.with_body_enhance(0)
        self.game_data["badge_cycle"] = self.game_data.get("badge_cycle", 0) + 1
        self._persist_ship_progress()

        return (
            "💾 본체 강화를 정산했습니다!\n\n"
            f"정산 대상: {sold_title}\n"
            f"정산한 본체 강화: +{sold_level}\n"
            f"정산 보상: {sell_price}G\n"
            f"현재 골드: {self.get_user_points()}G\n\n"
            f"유지: 등급 {self.ship_progress.grade.value} · 파츠 {self.ship_progress.format_parts_summary()}\n"
            "본체 +N만 초기화됩니다. 다시 업그레이드해봐요!"
        )

    # ========== 활동 관련 메서드 ==========

    def _get_activity_type(self, name: str) -> Optional[ActivityType]:
        name_lower = name.lower()
        for activity in self.activities:
            if name_lower == activity.name.lower() or name_lower in activity.prompts:
                return activity
        return None

    def _has_challenge_pass(self) -> bool:
        """구조 임무 진행 가능 여부. point_system 없으면 로컬 플레이로 패스 제한 없음."""
        if not self.point_system:
            return True
        return self._get_challenge_passes() > 0

    def _select_random_activity(self) -> ActivityType:
        """출동 시 이벤트 타입을 가중치 랜덤으로 결정.

        구조 이벤트는 패스가 있을 때만 후보에 포함된다.
        기존 hunt_normal/special/boss 통계 키는 실제 출현 이벤트 기준으로 유지된다.
        """
        candidates: list[ActivityType] = []
        weights: list[int] = []
        can_rescue = self._has_challenge_pass()

        for activity in self.activities:
            if activity.name == "구조" and not can_rescue:
                continue
            candidates.append(activity)
            weights.append(max(activity.weight, 1))

        if not candidates:
            # 방어적 폴백: 항상 정찰은 존재해야 함
            return self.activities[0]

        return random.choices(candidates, weights=weights, k=1)[0]

    def _perform_mission(self) -> str:
        """통합 출동: 랜덤 이벤트를 고른 뒤 기존 활동 보상/실패 흐름을 실행."""
        activity = self._select_random_activity()
        return self._perform_activity(activity)

    def _calculate_activity_reward(self, activity: ActivityType) -> int:
        body = self.ship_progress.body_enhance
        reward_multiplier = 1.0 + (
            body * (activity.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER)
        )
        base_reward = random.randint(*activity.reward_range)
        reward = int((activity.base_reward + base_reward) * reward_multiplier)

        # 주 엔진 파츠: 탐사 보상 +x% (탐사에 풀 적용, 그 외 절반)
        engine_bonus = self.ship_progress.part("engine").passive_value()
        if activity.name != "탐사":
            engine_bonus *= 0.5
        if engine_bonus > 0:
            reward = int(reward * (1.0 + engine_bonus / 100.0))

        # 기체 도감 grade는 드롭 티어/표시용. 보상 배율은 본체 +N·파츠 패시브가 담당.
        if random.random() < 0.08:
            reward = int(reward * random.choice((1.5, 1.75, 2.0)))
        return max(reward, 1)

    def _try_roll_loot_reward(self) -> Optional[dict]:
        """낮은 확률의 즉시 득템 보상. 도감 grade와 독립된 경제 보상."""
        roll = random.random()
        cumulative = 0.0
        for loot in self.loot_table:
            cumulative += loot.chance
            if roll < cumulative:
                amount = random.randint(*loot.gold_range)
                if self.point_system:
                    self.award_gold(amount, f"득템: {loot.name}")
                return {"loot": loot, "amount": amount}
        return None

    def _try_discover_ship(self, activity: ActivityType) -> Optional[tuple[CollectibleShip, dict]]:
        discovery_chance = {"정찰": 0.08, "탐사": 0.18, "구조": 0.35}.get(activity.name, 0.10)
        if random.random() >= discovery_chance:
            return None
        ship = self._roll_collectible_ship()
        return ship, self._grant_ship_to_collection(ship)

    def _perform_activity(self, activity: ActivityType | str) -> str:
        """개별 활동 실행. 통합 출동에서 선택된 ActivityType 또는 이름 문자열을 받는다."""
        if isinstance(activity, str):
            resolved = self._get_activity_type(activity)
            if resolved is None:
                return "❌ 해당 활동을 찾을 수 없습니다. '출동'으로 임무를 진행해 주세요."
            activity = resolved

        if activity.name == "구조":
            if not self._use_challenge_pass():
                passes = self._get_challenge_passes()
                return (
                    "❌ 구조 임무 패스가 부족합니다.\n"
                    f"보유 패스: {passes}장\n"
                    "출동 중 탐사 이벤트가 나오면 패스를 얻을 수 있어요."
                )

        success_rate = self._calculate_success_rate(activity)
        pilot_name = self.explorer_profile.call_sign if self.explorer_profile else "탐사대"
        event_header = f"🎲 랜덤 이벤트: {activity.icon} {activity.name}"

        if random.random() * 100 < success_rate:
            reward = self._calculate_activity_reward(activity)
            if self.point_system:
                self.award_gold(reward, f"{activity.name} 성공 ({pilot_name})")

            self.activity_count += 1
            self.total_reward += reward
            self.activity_stats[activity.name] = self.activity_stats.get(activity.name, 0) + 1
            self.game_data["activity_count"] = self.activity_count
            self.game_data["total_reward"] = self.total_reward
            self.game_data["activity_stats"] = self.activity_stats

            if self.point_system:
                activity_map = {"정찰": "hunt_normal", "탐사": "hunt_special", "구조": "hunt_boss"}
                update_params = {
                    "user_id": self.user_id,
                    "total_hunts": 1,
                    "total_hunt_reward": reward,
                }
                update_params[activity_map[activity.name]] = 1
                self.point_system.update_game_stats(**update_params)

            reward_multiplier = (
                activity.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER
            ) * 100
            description = random.choice(activity.success_messages).format(pilot=pilot_name)

            ship_title = self.ship_progress.format_title(self._equipped_ship_name())
            result_lines = [
                f"✅ {activity.name} 성공!",
                event_header,
                "",
                description,
                f"💰 리워드 +{reward}G (본체 +{self.ship_progress.body_enhance}강, 배율 {reward_multiplier:.1f}%)",
                f"🚀 현재 기체: {ship_title}",
                "",
            ]

            discovery = self._try_discover_ship(activity)
            if discovery:
                ship, collection_result = discovery
                new_badge = "NEW!" if collection_result.get("is_new") else f"중복 x{collection_result.get('count', 1)}"
                result_lines.append(
                    f"🚀 우주선 발견: 등급 {ship.grade} [{ship.name}] "
                    f"({GRADE_TONES[ship.ship_grade]}, {new_badge})"
                )
                equip_msg = self._maybe_equip_discovered_ship(ship)
                if equip_msg:
                    result_lines.append(equip_msg)
                result_lines.append(f"📚 도감: {len(self._get_collection_records())}/{len(self.ship_catalog)}종")
                result_lines.append("")

            loot_reward = self._try_roll_loot_reward()
            if loot_reward:
                loot = loot_reward["loot"]
                amount = loot_reward["amount"]
                self.total_reward += amount
                self.game_data["total_reward"] = self.total_reward
                if self.point_system:
                    self.point_system.update_game_stats(user_id=self.user_id, total_hunt_reward=amount)
                result_lines.append(f"{loot.icon} 득템! {loot.name} +{amount}G")
                result_lines.append(f"└ {loot.message}")
                result_lines.append("")

            if activity.name == "탐사":
                if random.random() < Config.BOSS_TICKET_DROP_RATE:
                    new_passes = self._add_challenge_pass()
                    result_lines.append(f"🎫 구조 임무 패스 획득! (현재: {new_passes}장)")
                    result_lines.append("")

            result_lines.extend(
                [
                    "활동 통계:",
                    f"- 정찰: {self.activity_stats.get('정찰', 0)}회",
                    f"- 탐사: {self.activity_stats.get('탐사', 0)}회",
                    f"- 구조: {self.activity_stats.get('구조', 0)}회",
                    f"총 활동: {self.activity_count}회",
                    f"총 획득 골드: {self.total_reward}G",
                    f"현재 골드: {self.get_user_points()}G",
                ]
            )

            return "\n".join(result_lines)

        description = random.choice(activity.fail_messages)
        return (
            f"❌ {activity.name}이(가) 잘 풀리지 않았어요...\n"
            f"{event_header}\n\n"
            f"{description}\n"
            "다시 출동해볼까요?"
            f"\n\n현재 성공 확률: {success_rate:.1f}%"
        )

    def _show_ship_codex(self) -> str:
        """수집한 우주선 도감 표시 — F~S 등급 단위 그룹핑 (희귀도 그룹 없음)."""
        collection = self._get_collection_records()
        total = len(self.ship_catalog)
        owned = len(collection)
        active = self.ship_progress.format_title(self._equipped_ship_name())
        lines = [
            "📚 우주선 도감",
            "",
            f"수집 현황: {owned}/{total}종 ({owned / total * 100:.0f}%)",
            f"주력 기체: {active}",
            "도감 티어는 기체 등급 F~S 만 사용합니다.",
            "파츠에는 등급이 없고 패시브·+N강만 있습니다.",
            "",
        ]

        for grade in GRADE_ORDER:
            ships = [ship for ship in self.ship_catalog if ship.ship_grade == grade]
            owned_count = sum(1 for ship in ships if ship.ship_id in collection)
            lines.append(
                f"{grade.value} {owned_count}/{len(ships)} · {GRADE_TONES[grade]}"
            )
            if not ships:
                lines.append("- (등록 기체 없음)")
                lines.append("")
                continue
            for ship in ships:
                count = collection.get(ship.ship_id, 0)
                if count:
                    duplicate_text = f" x{count}" if count > 1 else ""
                    equipped = " ★주력" if ship.ship_id == self.ship_progress.equipped_ship_id else ""
                    lines.append(f"- {ship.name}{duplicate_text}{equipped}: {ship.flavor}")
                else:
                    lines.append("- ???")
            lines.append("")

        lines.append(
            "💡 '출동' 성공 시 이벤트에 따라 정찰 8% / 탐사 18% / 구조 35% 확률로 우주선을 발견합니다."
        )
        lines.append("💡 상위 등급 발견 시 본체 +N이 등가 환산으로 계승됩니다 (예: F+100 → E+1).")
        return "\n".join(lines).rstrip()

    def _show_passes(self) -> str:
        passes = self._get_challenge_passes()
        drop_rate_percent = Config.BOSS_TICKET_DROP_RATE * 100

        return (
            "🎫 구조 임무 패스 현황\n\n"
            f"보유 패스: {passes}장\n\n"
            f"💡 '출동' 중 탐사 이벤트가 나오면 {drop_rate_percent:.0f}% 확률로 패스를 얻을 수 있어요!\n"
            "패스가 있으면 출동 시 구조 이벤트도 랜덤으로 등장합니다."
        )

    def _get_status(self) -> str:
        cost = self._calculate_cost()
        success_rate = self._calculate_success_rate()
        sell_price = self._calculate_sell_price()
        passes = self._get_challenge_passes()
        body = self.ship_progress.body_enhance

        status_lines = [
            "📊 현재 상태",
            "",
            "✨ 기체 체계:",
            *self.ship_progress.format_status_block(self._equipped_ship_name()),
            f"- 우주선 도감: {len(self._get_collection_records())}/{len(self.ship_catalog)}종",
            f"- 다음 본체 강화 비용: {cost}G",
            f"- 강화 성공률: {success_rate:.1f}%",
            f"- 정산 예상 보상: {sell_price}G",
            "",
            "🎯 임무 정보:",
            f"- 보상 배율: {1.0 + (body * Config.MONSTER_HUNT_REWARD_MULTIPLIER):.2f}배",
            f"- 구조 패스: {passes}장",
            "",
            "📈 통계:",
            f"- 강화 시도: {self.game_data.get('attempts', 0)}회",
            f"- 강화 성공: {self.game_data.get('successes', 0)}회",
            f"- 강화 실패: {self.game_data.get('failures', 0)}회",
            f"- 정찰: {self.activity_stats.get('정찰', 0)}회",
            f"- 탐사: {self.activity_stats.get('탐사', 0)}회",
            f"- 구조: {self.activity_stats.get('구조', 0)}회",
            f"- 총 활동: {self.activity_count}회",
            f"- 총 획득 골드: {self.total_reward}G",
            f"- 현재 골드: {self.get_user_points()}G",
        ]

        if self.explorer_profile:
            status_lines.extend(
                [
                    "",
                    "🛰️ 탐사대 프로필:",
                    f"- 콜사인: {self.explorer_profile.call_sign}",
                    f"- 역할: {self.explorer_profile.role}",
                    f"- 모듈: {self.explorer_profile.module}",
                    f"- 기질: {self.explorer_profile.temperament}",
                ]
            )

        return "\n".join(status_lines)

    def end(self) -> str:
        title = self.ship_progress.format_title(self._equipped_ship_name())
        attempts = self.game_data.get("attempts", 0)
        successes = self.game_data.get("successes", 0)
        failures = self.game_data.get("failures", 0)
        stats = self.activity_stats.copy()
        activity_count = self.activity_count
        reward = self.total_reward

        if self.point_system:
            self.point_system.set_game_stats(
                user_id=self.user_id,
                enhancement_attempts=attempts,
                enhancement_successes=successes,
                enhancement_failures=failures,
                hunt_normal=stats.get("정찰", 0),
                hunt_special=stats.get("탐사", 0),
                hunt_boss=stats.get("구조", 0),
                total_hunts=activity_count,
                total_hunt_reward=reward,
            )
            self._persist_ship_progress()

        self.is_active = False
        self.game_data.clear()

        return (
            "게임이 종료되었습니다.\n\n"
            "✨ 기체 요약:\n"
            f"- 최종 기체: {title}\n"
            f"- 파츠: {self.ship_progress.format_parts_summary()}\n"
            f"- 총 시도: {attempts}회 (성공 {successes}회 / 실패 {failures}회)\n\n"
            "🎯 임무 기록:\n"
            f"- 정찰: {stats.get('정찰', 0)}회\n"
            f"- 탐사: {stats.get('탐사', 0)}회\n"
            f"- 구조: {stats.get('구조', 0)}회\n"
            f"- 총 활동: {activity_count}회\n"
            f"- 총 획득 골드: {reward}G"
        )

    def get_help(self) -> str:
        drop_rate = Config.BOSS_TICKET_DROP_RATE * 100
        return (
            "우주 탐험 로그 도움말:\n\n"
            "✨ 기체 체계 (F~S 등급 · 본체 +N · 파츠 +N):\n"
            "- 강화: '성장', 'train', '업그레이드' → 본체 +N (+ 랜덤 파츠 +1)\n"
            "- 파츠에는 등급이 없고 패시브·강화만 있습니다 (엔진/센서/장갑).\n"
            "- 상위 등급 기체 발견 시 본체 +N이 등가 환산됩니다 (F+100 ≈ E+1).\n"
            "- 성공선에 가까울수록 더 큰 축하 이펙트/보너스가 터져요.\n"
            "- 실패 직후 5% 구간·장갑 패시브가 단계 하락을 막을 수 있어요.\n"
            "- 정산: '정산' 또는 'sell' (본체 +N 리셋 후 보상, 등급/파츠 유지)\n"
            "- 상태: '상태' 또는 'status'\n\n"
            "🎯 임무 (통합 출동):\n"
            "- 출동: '출동', 'mission', '탐험', 'go' (정찰·탐사·구조 중 랜덤 이벤트)\n"
            f"  · 정찰: 기본 센서 임무 (출현 비중 높음)\n"
            f"  · 탐사: 샘플 채취, 패스 드랍 확률 {drop_rate:.0f}%\n"
            "  · 구조: 고난도 구조 임무 (패스 1장 소모, 패스 있을 때만 등장)\n"
            "- 기존 '정찰'/'탐사'/'구조' 입력도 출동 alias로 동작합니다.\n"
            "- 패스 확인: '패스', 'ticket'\n"
            "- 도감 확인: '도감', 'collection'\n\n"
            "💡 임무 성공 시 우주선 발견/득템 보너스가 낮은 확률로 터집니다."
        )

    # ========== 패스 관련 유틸리티 ==========

    def _get_challenge_passes(self) -> int:
        if not self.point_system:
            return 0
        return self.point_system.get_boss_tickets(self.user_id)

    def _add_challenge_pass(self, amount: int = 1) -> int:
        if not self.point_system:
            return amount
        return self.point_system.add_boss_ticket(self.user_id, amount, "구조 패스 획득")

    def _use_challenge_pass(self, amount: int = 1) -> bool:
        if not self.point_system:
            return True
        return self.point_system.use_boss_ticket(self.user_id, amount, "구조 임무 진행")
