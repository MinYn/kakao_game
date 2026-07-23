import hashlib
import random
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Sequence

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
from events.telemetry import (
    track_enhance_result,
    track_mission_result,
    track_screen,
    track_ship_drop,
)
from ui.mobile_reply import MobileReply, MobileReplyBuilder, fit_text
from ui.result_template import (
    EMOJI,
    build_detail_slots,
    loop_cta_buttons,
)
from ui.screens import (
    D0_HOME,
    D1_CODEX,
    D1_GROW,
    D1_STATUS,
    D2_CODEX_PAGE,
    D2_ENHANCE_RESULT,
    D2_MISSION_RESULT,
    D2_PASS,
    D2_SELL_RESULT,
    D2_STATUS_DETAIL,
    D3_CODEX_PAGE,
    ScreenDef,
    get_registry,
    resolve_screen_for_command,
)


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
        # 모바일 depth UI 상태
        self.last_screen_id: str = D0_HOME.screen_id
        self.codex_page: int = 0
        self._reply_builder = MobileReplyBuilder()
        self._last_reply: Optional[MobileReply] = None
        # 이슈 #19 soft pity / 일일 목표 (세션 + game_data)
        self.mission_fail_streak: int = 0
        self.enhance_fail_streak: int = 0
        self.daily_date: str = date.today().isoformat()
        self.daily_missions: int = 0
        self.daily_enhances: int = 0

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
        """기체 발견 시 장착. 등급이 바뀌면 본체 +N 등가 계승 (첫 장착 포함). 파츠 +N 유지.

        반환 문자열은 모바일 슬롯용 짧은 훅 라인 (≤25자 권장).
        승급/계승 시 전용 피크 문구.
        """
        current = self.ship_progress
        prev_grade = current.grade

        # 첫 장착: 항상 equip_ship 경로 (등급 다르면 inherit, 동급이면 +N 유지)
        if current.equipped_ship_id is None:
            next_progress, _new_n = current.equip_ship(
                ship.ship_id, ship.grade, inherit=True
            )
            self.ship_progress = next_progress
            self._persist_ship_progress()
            if parse_grade(ship.grade) != prev_grade:
                return (
                    f"{EMOJI['up']} 계승 {prev_grade.value}→"
                    f"{next_progress.grade.value}+{next_progress.body_enhance}"
                )
            return (
                f"🛠️ 장착 {ship.name} {format_grade_mark(ship.grade)}"
            )

        if not is_higher_grade(ship.grade, current.grade):
            return None

        next_progress, _new_n = current.equip_ship(ship.ship_id, ship.grade, inherit=True)
        self.ship_progress = next_progress
        self._persist_ship_progress()
        # F+100→E+1 등 계승 전용 피크
        return (
            f"{EMOJI['up']} 계승 {prev_grade.value}→"
            f"{next_progress.grade.value}+{next_progress.body_enhance}"
        )

    def _duplicate_ship_gold(self, grade: str) -> int:
        """도감 중복 획득 시 항상 지급되는 보호 보상."""
        table = getattr(Config, "DUPLICATE_SHIP_GOLD", None) or {}
        return int(table.get(str(grade).upper(), 15))

    def _ensure_daily_bucket(self) -> None:
        """자정 넘기면 일일 카운터 리셋."""
        today = date.today().isoformat()
        if self.daily_date != today:
            self.daily_date = today
            self.daily_missions = 0
            self.daily_enhances = 0

    def _bump_daily_mission(self) -> None:
        self._ensure_daily_bucket()
        self.daily_missions += 1

    def _bump_daily_enhance(self) -> None:
        self._ensure_daily_bucket()
        self.daily_enhances += 1

    def _daily_home_line(self) -> str:
        """홈 1줄: 일일 미니 목표 진행."""
        self._ensure_daily_bucket()
        m_goal = Config.DAILY_MISSION_GOAL
        e_goal = Config.DAILY_ENHANCE_GOAL
        return (
            f"{EMOJI['daily']} 출동{self.daily_missions}/{m_goal} "
            f"강화{self.daily_enhances}/{e_goal}"
        )

    def _mission_pity_boost(self) -> float:
        return min(
            self.mission_fail_streak * Config.MISSION_PITY_PER_FAIL,
            Config.MISSION_PITY_CAP,
        )

    def _enhance_pity_boost(self) -> float:
        return min(
            self.enhance_fail_streak * Config.ENHANCE_PITY_PER_FAIL,
            Config.ENHANCE_PITY_CAP,
        )

    def _mission_cta_buttons(self) -> list[dict]:
        rate = self._calculate_success_rate()
        return loop_cta_buttons(
            primary_label="🚀 다시 출동",
            primary_message="출동",
            secondary_label=f"🔨 강화 {rate:.0f}%",
            secondary_message="강화",
        )

    def _enhance_cta_buttons(self) -> list[dict]:
        rate = self._calculate_success_rate()
        return loop_cta_buttons(
            primary_label=f"🔨 다시 {rate:.0f}%",
            primary_message="강화",
            secondary_label="🚀 출동",
            secondary_message="출동",
        )

    def _sell_cta_buttons(self) -> list[dict]:
        return loop_cta_buttons(
            primary_label="🔨 강화",
            primary_message="강화",
            secondary_label="🚀 출동",
            secondary_message="출동",
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
        """구조화된 커맨드 정의 (모바일 depth 화면과 대응)."""
        return [
            {
                "key": "home",
                "triggers": ["홈", "home", "hub", "시작"],
                "handler": self._show_home,
            },
            {
                # D1 성장 메뉴 (실제 강화는 key=enhance)
                "key": "grow_menu",
                "triggers": ["성장", "grow"],
                "handler": self._show_grow_menu,
                "button": {"label": "🔨 성장", "messageText": "성장"},
            },
            {
                "key": "enhance",
                "triggers": ["강화", "업그레이드", "개조", "train"],
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
                # D1 상태 메뉴
                "key": "status_menu",
                "triggers": ["상태", "status", "info"],
                "handler": self._show_status_menu,
                "button": {"label": "📊 상태", "messageText": "상태"},
            },
            {
                "key": "status_detail",
                "triggers": ["상세", "상태상세"],
                "handler": self._get_status,
                "button": {"label": "📋 상세", "messageText": "상세"},
            },
            {
                # D1 도감 메뉴
                "key": "codex_menu",
                "triggers": ["도감", "collection", "codex", "수집", "ships"],
                "handler": self._show_codex_menu,
                "button": {"label": "📚 도감", "messageText": "도감"},
            },
            {
                "key": "codex_list",
                "triggers": ["목록"],
                "handler": self._show_codex_first_page,
            },
            {
                "key": "codex_next",
                "triggers": ["다음"],
                "handler": self._show_codex_next_page,
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
        """현재(또는 직전 명령) 화면의 모바일 버튼 반환 — 정확히 2 또는 4개."""
        screen_id = self.last_screen_id
        if last_command:
            screen = resolve_screen_for_command(last_command)
            # 홈/메뉴 명령은 resolve 우선, 결과 화면은 last_screen 유지가 더 정확
            if screen.screen_id.startswith("D0") or screen.screen_id.startswith("D1"):
                screen_id = screen.screen_id
            elif self.last_screen_id:
                screen_id = self.last_screen_id
            else:
                screen_id = screen.screen_id

        if self._last_reply and self._last_reply.buttons:
            return list(self._last_reply.buttons)

        return get_registry().buttons_for(screen_id or D0_HOME.screen_id)

    def _commit_reply(self, reply: MobileReply) -> str:
        """화면 상태를 갱신하고 포맷된 텍스트를 반환."""
        self._last_reply = reply
        self.last_screen_id = reply.screen_id
        return reply.text

    def _reply_for_screen(
        self,
        screen: ScreenDef,
        lines: List[str] | str,
        buttons: Optional[Sequence[dict]] = None,
    ) -> str:
        btn_list = list(buttons) if buttons is not None else screen.button_dicts()
        reply = self._reply_builder.build(
            lines,
            screen.layout,
            btn_list,
            screen_id=screen.screen_id,
            depth=screen.depth,
        )
        return self._commit_reply(reply)

    def _show_home(self) -> str:
        """D0 홈 MENU — 일일 미니 목표 1줄 포함 (이슈 #19 P4)."""
        ship_title = self.ship_progress.format_title(self._equipped_ship_name())
        gold = self.get_user_points()
        call_sign = self.explorer_profile.call_sign if self.explorer_profile else "—"
        lines = [
            "🛰️ 우주 탐험 홈",
            f"콜사인 {call_sign}",
            f"기체 {ship_title}",
            f"골드 {gold}G",
            self._daily_home_line(),
        ]
        track_screen(self.user_id, D0_HOME.screen_id, command="홈")
        return self._reply_for_screen(D0_HOME, lines)

    def _show_grow_menu(self) -> str:
        """D1 성장 MENU."""
        ship_title = self.ship_progress.format_title(self._equipped_ship_name())
        cost = self._calculate_cost()
        rate = self._calculate_success_rate()
        lines = [
            "🔨 성장 메뉴",
            f"{ship_title}",
            f"강화비용 {cost}G",
            f"성공률 {rate:.0f}%",
            f"골드 {self.get_user_points()}G",
        ]
        return self._reply_for_screen(D1_GROW, lines)

    def _show_status_menu(self) -> str:
        """D1 상태 MENU."""
        ship_title = self.ship_progress.format_title(self._equipped_ship_name())
        passes = self._get_challenge_passes()
        lines = [
            "📊 상태 메뉴",
            f"{ship_title}",
            f"골드 {self.get_user_points()}G",
            f"패스 {passes}장",
            "항목을 선택하세요",
        ]
        return self._reply_for_screen(D1_STATUS, lines)

    def _show_codex_menu(self) -> str:
        """D1 도감 MENU."""
        owned = len(self._get_collection_records())
        total = len(self.ship_catalog)
        active = self.ship_progress.format_title(self._equipped_ship_name())
        lines = [
            "📚 도감",
            f"수집 {owned}/{total}종",
            f"주력 {active}",
            "목록·다음으로 열람",
            "내 기체=상세 상태",
        ]
        self.codex_page = 0
        return self._reply_for_screen(D1_CODEX, lines)

    def _codex_page_lines(self, page: int) -> tuple[List[str], int]:
        """도감 페이지 라인 생성. (lines, total_pages) 반환."""
        collection = self._get_collection_records()
        total = len(self.ship_catalog)
        owned = len(collection)
        # 페이지당 본문 약 12줄 (헤더 3줄 제외)
        entries: List[str] = []
        for grade in GRADE_ORDER:
            ships = [s for s in self.ship_catalog if s.ship_grade == grade]
            owned_count = sum(1 for s in ships if s.ship_id in collection)
            entries.append(f"{grade.value} {owned_count}/{len(ships)}")
            for ship in ships:
                count = collection.get(ship.ship_id, 0)
                if count:
                    mark = "★" if ship.ship_id == self.ship_progress.equipped_ship_id else ""
                    dup = f"x{count}" if count > 1 else ""
                    entries.append(f"-{ship.name}{dup}{mark}")
                else:
                    entries.append("-???")

        per_page = 12
        total_pages = max(1, (len(entries) + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        chunk = entries[page * per_page : (page + 1) * per_page]
        header = [
            f"📚 도감 {page + 1}/{total_pages}",
            f"수집 {owned}/{total}종",
            f"주력 {self.ship_progress.format_title(self._equipped_ship_name())}",
        ]
        return header + chunk, total_pages

    def _show_codex_page(self, page: int) -> str:
        lines, total_pages = self._codex_page_lines(page)
        self.codex_page = page
        # page 0 → D2, page>=1 → D3 (depth 최대 3, 더 깊어지면 홈으로 접히는 대신 D3 유지)
        screen = D2_CODEX_PAGE if page == 0 else D3_CODEX_PAGE
        return self._reply_for_screen(screen, lines)

    def _show_codex_first_page(self) -> str:
        return self._show_codex_page(0)

    def _show_codex_next_page(self) -> str:
        _, total_pages = self._codex_page_lines(self.codex_page)
        next_page = (self.codex_page + 1) % total_pages
        return self._show_codex_page(next_page)

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
        """게임 시작 — D0 홈 MENU (모바일 5줄+버튼4)."""
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
        self.codex_page = 0
        return self._show_home()

    def process_command(self, command: str) -> str:
        """명령 처리 — 모바일 화면 단위 응답. 시작 메시지와 결과 중복 연결 안 함."""
        if not self.is_active:
            self.start()

        response, key = self.run_structured_command(command)
        if response:
            return response

        # 알 수 없는 명령 → D0 홈
        return self._show_home()

    # ========== 성장 관련 메서드 ==========

    def _effective_power(self) -> float:
        """등급·본체 +N 등가 스탯. F+100 과 E+1 이 동일 (core_stat)."""
        return float(self.ship_progress.core_stat())

    def _calculate_cost(self) -> int:
        """본체 +N 강화 비용 계산 (현재 등급의 +N 기준 투자)."""
        cost = int(
            self.enhancement_cost_base
            * (self.enhancement_cost_multiplier ** self.ship_progress.body_enhance)
        )
        return max(cost, 10)

    def _calculate_success_rate(
        self,
        activity: Optional[ActivityType] = None,
        *,
        apply_pity: bool = True,
    ) -> float:
        """성공 확률 계산. 등가 스탯(core_stat) + 센서 파츠 + soft pity."""
        base_rate = activity.success_rate if activity else 80.0
        # raw body_enhance 가 아니라 등급 등가 스탯 사용 → F+100 ≈ E+1
        body_boost = self._effective_power() * 2
        sensor_boost = self.ship_progress.part("sensor").passive_value()
        if activity and activity.name != "정찰":
            # 센서 패시브는 정찰에 더 크게, 그 외 활동은 절반 반영
            sensor_boost *= 0.5
        pity = 0.0
        if apply_pity:
            if activity is not None:
                pity = self._mission_pity_boost()
            else:
                pity = self._enhance_pity_boost()
        boosted = min(base_rate + body_boost + sensor_boost + pity, 98.0)
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
        """정산 금액 계산 (본체 body_enhance 기준)."""
        body = self.ship_progress.body_enhance
        if body == 0:
            return 0

        total_invested = 0
        for level in range(body):
            level_cost = int(
                self.enhancement_cost_base * (self.enhancement_cost_multiplier ** level)
            )
            total_invested += max(level_cost, 10)

        sell_price = int(total_invested * self.sell_multiplier)
        level_bonus_amount = body * self.level_bonus
        sell_price += level_bonus_amount

        if body >= 10:
            sell_price += int(sell_price * 0.2)
        elif body >= 5:
            sell_price += int(sell_price * 0.1)

        return max(sell_price, 10)

    def _enhance(self) -> str:
        """기체 본체 +N 강화 — D2_ENHANCE_RESULT DETAIL (훅→수치→CTA)."""
        cost = self._calculate_cost()
        before = self.ship_progress.body_enhance
        ship_title = self.ship_progress.format_title(self._equipped_ship_name())
        screen = D2_ENHANCE_RESULT
        cta_btns = self._enhance_cta_buttons()

        if not self.point_system or not self.point_system.has_gold(self.user_id, cost):
            lines = build_detail_slots(
                hook=f"{EMOJI['fail']} 골드 부족",
                metrics=[f"필요 {cost}G", f"보유 {self.get_user_points()}G", ship_title],
                progress=[f"다음 성공률 {self._calculate_success_rate():.0f}%"],
                cta="출동으로 골드 확보",
            )
            return self._reply_for_screen(screen, lines, buttons=cta_btns)

        self.deduct_gold(cost, f"본체 강화 시도 ({ship_title} +{before} → +{before + 1})")
        self._bump_daily_enhance()

        self.game_data["attempts"] = self.game_data.get("attempts", 0) + 1
        if self.point_system:
            self.point_system.update_game_stats(user_id=self.user_id, enhancement_attempts=1)

        success_rate = self._calculate_success_rate()
        roll = random.random() * 100
        is_success = roll < success_rate
        margin = success_rate - roll

        if is_success:
            self.ship_progress = self.ship_progress.with_body_enhance(before + 1)
            part_id = random.choice(list(PART_CATALOG.keys()))
            part_before = self.ship_progress.parts.get(part_id, 0)
            self.ship_progress = self.ship_progress.with_part_enhance(part_id, part_before + 1)
            self._persist_ship_progress()
            self.game_data["successes"] = self.game_data.get("successes", 0) + 1
            self.enhance_fail_streak = 0
            if self.point_system:
                self.point_system.update_game_stats(user_id=self.user_id, enhancement_successes=1)

            after = before + 1
            next_cost = self._calculate_cost()
            next_rate = self._calculate_success_rate()
            celebration = self._get_enhancement_celebration(roll, success_rate)
            part_def = PART_CATALOG[part_id]
            milestones = set(Config.ENHANCE_MILESTONES)

            bonus_lines: List[str] = []
            if celebration:
                bonus = max(int(cost * celebration.gold_multiplier), 10)
                self.award_gold(bonus, f"강화 축하 이펙트: {celebration.name}")
                bonus_lines.extend(
                    [
                        f"{celebration.icon} {celebration.name}",
                        f"보너스 +{bonus}G",
                    ]
                )
            if after in milestones:
                mile_gold = Config.ENHANCE_MILESTONE_GOLD_BASE * max(1, after // 5)
                self.award_gold(mile_gold, f"강화 마일스톤 +{after}")
                stage = body_enhance_to_upgrade_stage(after)
                bonus_lines.extend(
                    [
                        f"{EMOJI['up']} 마일스톤 +{after}",
                        f"배지 stage {stage} ·+{mile_gold}G",
                    ]
                )

            lines = build_detail_slots(
                hook=f"{EMOJI['success']} 강화 성공!",
                metrics=[
                    self.ship_progress.format_title(self._equipped_ship_name()),
                    f"본체 +{before}→+{after}",
                    f"파츠 {part_def.name}+{part_before + 1}",
                ],
                bonus=bonus_lines,
                progress=[
                    f"다음 {next_cost}G {next_rate:.0f}%",
                    f"골드 {self.get_user_points()}G",
                ],
                cta="한 번 더 강화?",
            )
            track_enhance_result(
                self.user_id,
                success=True,
                margin=margin,
                celebration=celebration.name if celebration else None,
                body_enhance=after,
                extra={"milestone": after in milestones},
            )
            return self._reply_for_screen(
                screen, lines, buttons=self._enhance_cta_buttons()
            )

        self.game_data["failures"] = self.game_data.get("failures", 0) + 1
        self.enhance_fail_streak += 1
        if self.point_system:
            self.point_system.update_game_stats(user_id=self.user_id, enhancement_failures=1)

        near_miss = self._is_enhancement_near_miss(roll, success_rate)
        armor_save = self.ship_progress.part("armor").passive_value()
        armor_proc = (
            self.ship_progress.body_enhance > 0
            and armor_save > 0
            and random.random() * 100 < min(armor_save, 25)
        )

        if self.ship_progress.body_enhance > 0 and (near_miss or armor_proc):
            lines = build_detail_slots(
                hook=f"{EMOJI['near_miss']} 아슬아슬 버팀!",
                metrics=[
                    f"성공률 {success_rate:.0f}%",
                    f"판정 {roll:.0f}%",
                    "본체 강화 유지",
                    self.ship_progress.format_title(self._equipped_ship_name()),
                ],
                progress=[
                    f"pity +{self._enhance_pity_boost():.0f}%",
                    f"골드 {self.get_user_points()}G",
                ],
                cta="한 번 더?",
            )
            track_enhance_result(
                self.user_id,
                success=False,
                margin=margin,
                near_miss=True,
                body_enhance=self.ship_progress.body_enhance,
            )
            return self._reply_for_screen(
                screen, lines, buttons=self._enhance_cta_buttons()
            )

        if self.ship_progress.body_enhance > 0:
            self.ship_progress = self.ship_progress.with_body_enhance(
                self.ship_progress.body_enhance - 1
            )
            self._persist_ship_progress()
            lines = build_detail_slots(
                hook=f"{EMOJI['fail']} 강화 하락",
                metrics=[
                    self.ship_progress.format_title(self._equipped_ship_name()),
                    f"골드 {self.get_user_points()}G",
                ],
                progress=[f"pity +{self._enhance_pity_boost():.0f}%"],
                cta="다시 도전!",
            )
            track_enhance_result(
                self.user_id,
                success=False,
                margin=margin,
                near_miss=False,
                body_enhance=self.ship_progress.body_enhance,
            )
            return self._reply_for_screen(
                screen, lines, buttons=self._enhance_cta_buttons()
            )

        lines = build_detail_slots(
            hook=f"{EMOJI['fail']} 강화 실패",
            metrics=[
                self.ship_progress.format_title(self._equipped_ship_name()),
                f"골드 {self.get_user_points()}G",
            ],
            progress=[f"pity +{self._enhance_pity_boost():.0f}%"],
            cta="다시 시도!",
        )
        track_enhance_result(
            self.user_id,
            success=False,
            margin=margin,
            near_miss=False,
            body_enhance=0,
        )
        return self._reply_for_screen(
            screen, lines, buttons=self._enhance_cta_buttons()
        )

    def _sell(self) -> str:
        """본체 강화 정산 — D2_SELL_RESULT DETAIL."""
        screen = D2_SELL_RESULT
        if self.ship_progress.body_enhance == 0:
            return self._reply_for_screen(
                screen,
                [
                    "❌ 정산 불가",
                    "본체 강화 없음",
                    "강화 후 정산하세요",
                    f"골드 {self.get_user_points()}G",
                ],
            )

        sell_price = self._calculate_sell_price()
        sold_level = self.ship_progress.body_enhance
        sold_title = self.ship_progress.format_title(self._equipped_ship_name())

        if self.point_system:
            self.award_gold(sell_price, f"본체 강화 정산 ({sold_title})")

        self.ship_progress = self.ship_progress.with_body_enhance(0)
        self.game_data["badge_cycle"] = self.game_data.get("badge_cycle", 0) + 1
        self._persist_ship_progress()

        lines = build_detail_slots(
            hook="💾 정산 완료",
            metrics=[
                sold_title,
                f"본체 +{sold_level} 정산",
                f"보상 +{sell_price}G",
            ],
            progress=[
                f"골드 {self.get_user_points()}G",
                f"등급 {self.ship_progress.grade.value} 유지",
                "파츠 유지",
            ],
            cta="다시 키워볼까요?",
        )
        return self._reply_for_screen(screen, lines, buttons=self._sell_cta_buttons())

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
        # 보상 배율도 등가 스탯 사용 → 승급 계승 후 파워 유지
        power = self._effective_power()
        reward_multiplier = 1.0 + (
            power * (activity.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER)
        )
        base_reward = random.randint(*activity.reward_range)
        reward = int((activity.base_reward + base_reward) * reward_multiplier)

        # 주 엔진 파츠: 탐사 보상 +x% (탐사에 풀 적용, 그 외 절반)
        engine_bonus = self.ship_progress.part("engine").passive_value()
        if activity.name != "탐사":
            engine_bonus *= 0.5
        if engine_bonus > 0:
            reward = int(reward * (1.0 + engine_bonus / 100.0))

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
        """개별 활동 실행 — D2_MISSION_RESULT DETAIL (훅→수치→CTA)."""
        screen = D2_MISSION_RESULT
        if isinstance(activity, str):
            resolved = self._get_activity_type(activity)
            if resolved is None:
                return self._reply_for_screen(
                    screen,
                    [f"{EMOJI['fail']} 활동 없음", "출동으로 진행하세요"],
                    buttons=self._mission_cta_buttons(),
                )
            activity = resolved

        if activity.name == "구조":
            if not self._use_challenge_pass():
                passes = self._get_challenge_passes()
                return self._reply_for_screen(
                    screen,
                    build_detail_slots(
                        hook=f"{EMOJI['fail']} 패스 부족",
                        metrics=[f"보유 {passes}장"],
                        progress=["탐사로 패스 획득"],
                        cta="다시 출동!",
                    ),
                    buttons=self._mission_cta_buttons(),
                )

        success_rate = self._calculate_success_rate(activity)
        pilot_name = self.explorer_profile.call_sign if self.explorer_profile else "탐사대"
        self._bump_daily_mission()

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
            self.mission_fail_streak = 0

            if self.point_system:
                activity_map = {"정찰": "hunt_normal", "탐사": "hunt_special", "구조": "hunt_boss"}
                update_params = {
                    "user_id": self.user_id,
                    "total_hunts": 1,
                    "total_hunt_reward": reward,
                }
                update_params[activity_map[activity.name]] = 1
                self.point_system.update_game_stats(**update_params)

            ship_title = self.ship_progress.format_title(self._equipped_ship_name())
            power = self._effective_power()
            metrics = [
                f"{activity.icon} {activity.name}",
                f"+{reward}G 스탯{power:.0f}",
                f"🚀 {ship_title}",
            ]
            bonus_lines: List[str] = []

            discovery = self._try_discover_ship(activity)
            if discovery:
                ship, collection_result = discovery
                is_new = bool(collection_result.get("is_new"))
                track_ship_drop(
                    self.user_id,
                    grade=ship.grade,
                    ship_id=ship.ship_id,
                    is_new=is_new,
                )
                if is_new:
                    # 신규 기체 = 최대 피크 연출
                    bonus_lines.append(f"{EMOJI['new']} NEW {ship.grade}급!")
                    bonus_lines.append(f"{EMOJI['celebrate']} {ship.name}")
                else:
                    # 중복 = 항상 보호 보상
                    dup_gold = self._duplicate_ship_gold(ship.grade)
                    if self.point_system:
                        self.award_gold(dup_gold, f"도감 중복: {ship.name}")
                    self.total_reward += dup_gold
                    self.game_data["total_reward"] = self.total_reward
                    if self.point_system:
                        self.point_system.update_game_stats(
                            user_id=self.user_id, total_hunt_reward=dup_gold
                        )
                    count = collection_result.get("count", 1)
                    bonus_lines.append(f"중복 {ship.name} x{count}")
                    bonus_lines.append(f"{EMOJI['loot']} 분해 +{dup_gold}G")
                equip_msg = self._maybe_equip_discovered_ship(ship)
                if equip_msg:
                    bonus_lines.append(fit_text(equip_msg, 1).split("\n")[0])
                bonus_lines.append(
                    f"도감 {len(self._get_collection_records())}/{len(self.ship_catalog)}"
                )

            loot_reward = self._try_roll_loot_reward()
            if loot_reward:
                loot = loot_reward["loot"]
                amount = loot_reward["amount"]
                self.total_reward += amount
                self.game_data["total_reward"] = self.total_reward
                if self.point_system:
                    self.point_system.update_game_stats(user_id=self.user_id, total_hunt_reward=amount)
                bonus_lines.append(f"{loot.icon} {loot.name}+{amount}G")

            if activity.name == "탐사":
                if random.random() < Config.BOSS_TICKET_DROP_RATE:
                    new_passes = self._add_challenge_pass()
                    bonus_lines.append(f"🎫 패스 획득({new_passes})")

            enhance_rate = self._calculate_success_rate()
            enhance_cost = self._calculate_cost()
            progress = [
                f"강화 {enhance_cost}G {enhance_rate:.0f}%",
                f"골드 {self.get_user_points()}G",
            ]
            lines = build_detail_slots(
                hook=f"{EMOJI['success']} {activity.name} 성공!",
                metrics=metrics,
                bonus=bonus_lines,
                progress=progress,
                cta="한 번 더 출동?",
            )
            track_mission_result(
                self.user_id,
                success=True,
                activity=activity.name,
                reward=reward,
                extra={"discovered": discovery is not None},
            )
            return self._reply_for_screen(
                screen, lines, buttons=self._mission_cta_buttons()
            )

        # 실패: 소형 보호 보상 + pity 스택 (완전 무보상 금지)
        self.mission_fail_streak += 1
        consol_min = Config.MISSION_FAIL_CONSOLATION_MIN
        consol_max = Config.MISSION_FAIL_CONSOLATION_MAX
        # 연속 실패 시 위로금 소폭 증가
        consol = random.randint(consol_min, consol_max) + min(self.mission_fail_streak - 1, 3)
        if self.point_system:
            self.award_gold(consol, f"{activity.name} 실패 위로")
        description = random.choice(activity.fail_messages)
        short_desc = fit_text(description, 1).split("\n")[0] if description else ""
        lines = build_detail_slots(
            hook=f"{EMOJI['fail']} {activity.name} 실패",
            metrics=[
                f"{activity.icon} {activity.name}",
                short_desc,
                f"성공률 {success_rate:.0f}%",
            ],
            bonus=[f"{EMOJI['pity']} 구조금 +{consol}G"],
            progress=[
                f"pity +{self._mission_pity_boost():.0f}%",
                f"골드 {self.get_user_points()}G",
            ],
            cta="다시 출동!",
        )
        track_mission_result(
            self.user_id,
            success=False,
            activity=activity.name,
            reward=consol,
            extra={"fail_streak": self.mission_fail_streak},
        )
        return self._reply_for_screen(
            screen, lines, buttons=self._mission_cta_buttons()
        )

    def _show_ship_codex(self) -> str:
        """하위 호환: 도감 명령은 메뉴로 진입."""
        return self._show_codex_menu()

    def _show_passes(self) -> str:
        passes = self._get_challenge_passes()
        drop_rate_percent = Config.BOSS_TICKET_DROP_RATE * 100
        return self._reply_for_screen(
            D2_PASS,
            [
                "🎫 구조 패스",
                f"보유 {passes}장",
                f"탐사 시 {drop_rate_percent:.0f}% 드랍",
                "패스 있으면 구조 등장",
                "출동으로 사용",
            ],
        )

    def _get_status(self) -> str:
        """D2 상태 상세 DETAIL (15줄 이내)."""
        cost = self._calculate_cost()
        success_rate = self._calculate_success_rate()
        sell_price = self._calculate_sell_price()
        passes = self._get_challenge_passes()
        ship_title = self.ship_progress.format_title(self._equipped_ship_name())
        power = self._effective_power()
        call_sign = self.explorer_profile.call_sign if self.explorer_profile else "—"

        lines = [
            "📊 상태 상세",
            f"{ship_title}",
            f"파츠 {self.ship_progress.format_parts_summary()}",
            f"스탯 {power:.0f}",
            f"강화 {cost}G {success_rate:.0f}%",
            f"정산예상 {sell_price}G",
            f"도감 {len(self._get_collection_records())}/{len(self.ship_catalog)}",
            f"패스 {passes}장",
            f"시도{self.game_data.get('attempts', 0)} "
            f"성공{self.game_data.get('successes', 0)} "
            f"실패{self.game_data.get('failures', 0)}",
            f"정찰{self.activity_stats.get('정찰', 0)} "
            f"탐사{self.activity_stats.get('탐사', 0)} "
            f"구조{self.activity_stats.get('구조', 0)}",
            f"총활 {self.activity_count}회",
            f"획득 {self.total_reward}G",
            f"골드 {self.get_user_points()}G",
            f"콜사인 {call_sign}",
        ]
        return self._reply_for_screen(D2_STATUS_DETAIL, lines)

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
        from ui.screens import D2_HELP

        lines = [
            "❓ 탐험 도움말",
            "성장→강화·판매",
            "출동=랜덤 임무",
            f"탐사 패스 {drop_rate:.0f}%",
            "구조=패스 1장",
            "등급 F~S 본체+N",
            "파츠+N 패시브",
            "도감 목록·다음",
            "상태=상세·골드",
            "홈으로 복귀",
        ]
        return self._reply_for_screen(D2_HELP, lines)

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
