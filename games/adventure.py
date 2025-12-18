import hashlib
import random
from dataclasses import dataclass
from typing import Dict, Optional

from games.base_game import Game
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
        self.current_level = 0
        self.enhancement_cost_base = Config.ENHANCEMENT_BASE_COST
        self.enhancement_cost_multiplier = Config.ENHANCEMENT_COST_MULTIPLIER
        self.sell_multiplier = Config.ENHANCEMENT_SELL_MULTIPLIER
        self.level_bonus = Config.ENHANCEMENT_LEVEL_BONUS

        self.activities = self._init_activities()
        self.activity_stats: Dict[str, int] = {a.name: 0 for a in self.activities}
        self.activity_count = 0
        self.total_reward = 0
        self.explorer_profile: Optional[ExplorerProfile] = None
        self.command_definitions = self._init_command_definitions()
        self._build_command_index()

    def _init_activities(self) -> list:
        """활동 타입 초기화"""
        return [
            ActivityType(
                name="정찰",
                base_reward=30,
                reward_range=(20, 45),
                multiplier=0.08,
                prompts=("정찰", "scout", "walk", "n", "1"),
                success_rate=86.0,
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
                "key": "passes",
                "triggers": ["패스", "ticket", "tickets", "t"],
                "handler": self._show_passes,
                "button": {"label": "🎫 패스", "messageText": "패스"},
            },
            {
                "key": "scout",
                "triggers": ["정찰", "walk", "scout", "n", "1"],
                "handler": lambda: self._perform_activity("정찰"),
                "button": {"label": "🛰️ 정찰", "messageText": "정찰"},
            },
            {
                "key": "survey",
                "triggers": ["탐사", "play", "survey", "s", "2", "특별놀이"],
                "handler": lambda: self._perform_activity("탐사"),
                "button": {"label": "🧭 탐사", "messageText": "탐사"},
            },
            {
                "key": "rescue",
                "triggers": ["구조", "challenge", "rescue", "boss", "b", "3"],
                "handler": lambda: self._perform_activity("구조"),
                "button": {"label": "🚨 구조", "messageText": "구조"},
            },
        ]

    def get_command_buttons(self, last_command: Optional[str] = None) -> list[dict]:
        """모험 게임용 버튼 우선순위 제공"""
        key_order = [
            "enhance",
            "scout",
            "survey",
            "rescue",
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
            return {
                "level": self.point_system.get_enhancement_level(self.user_id),
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
            "activity_count": 0,
            "total_reward": 0,
            "activity_stats": {"정찰": 0, "탐사": 0, "구조": 0},
            "attempts": 0,
            "successes": 0,
            "failures": 0,
        }

    def start(self) -> str:
        """게임 시작"""
        self.is_active = True
        self.explorer_profile = ExplorerProfile.from_user_id(self.user_id)
        stats = self._load_stats()

        self.current_level = stats["level"]
        self.activity_count = stats["activity_count"]
        self.total_reward = stats["total_reward"]
        self.activity_stats = stats["activity_stats"].copy()
        self.game_data = {
            "level": self.current_level,
            "attempts": stats["attempts"],
            "successes": stats["successes"],
            "failures": stats["failures"],
            "activity_count": self.activity_count,
            "total_reward": self.total_reward,
            "activity_stats": self.activity_stats,
        }

        challenge_passes = self._get_challenge_passes()
        pilot_card = (
            f"{self.explorer_profile.badge}\n"
            f"콜사인: {self.explorer_profile.call_sign}\n"
            f"역할: {self.explorer_profile.role}\n"
            f"기체: {self.explorer_profile.ship_class} ({self.explorer_profile.module})\n"
            f"기질: {self.explorer_profile.temperament}"
        )

        return (
            "🛰️ 우주 탐험 로그를 시작합니다!\n\n"
            f"{pilot_card}\n\n"
            f"현재 우주선 강화 레벨: +{self.current_level}\n"
            f"구조 임무 패스: {challenge_passes}장\n\n"
            "명령어:\n"
            "✨ 강화: '성장'/'train'/'강화'/'업그레이드' (골드 사용)\n"
            "💾 정산: '정산'/'sell' (강화 단계 초기화 후 보상)\n"
            "📊 상태보기: '상태'/'status'\n\n"
            "🎯 활동:\n"
            "- '정찰'/'scout': 기본 센서 임무\n"
            "- '탐사'/'survey': 샘플 채취 (패스 드랍 가능)\n"
            "- '구조'/'rescue': 패스를 사용한 고난도 구조 임무\n"
            "- '패스'/'ticket': 보유 구조 패스 확인"
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
            "사용 가능한 명령: 성장, 정산, 정찰, 탐사, 구조, 패스, 상태"
        )
        if start_message:
            return f"{start_message}\n\n{fallback}"
        return fallback

    # ========== 성장 관련 메서드 ==========

    def _calculate_cost(self) -> int:
        """우주선 강화 비용 계산"""
        cost = int(
            self.enhancement_cost_base
            * (self.enhancement_cost_multiplier ** self.current_level)
        )
        return max(cost, 10)

    def _calculate_success_rate(self, activity: Optional[ActivityType] = None) -> float:
        """성공 확률 계산"""
        base_rate = activity.success_rate if activity else 80.0
        boosted = min(base_rate + (self.current_level * 2), 98.0)
        return max(boosted, 25.0)

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
        """우주선 강화"""
        cost = self._calculate_cost()

        if not self.point_system or not self.point_system.has_gold(self.user_id, cost):
            return (
                "❌ 우주선 강화를 위한 골드가 부족합니다.\n"
                f"필요 골드: {cost}G\n현재 골드: {self.get_user_points()}G"
            )

        self.deduct_gold(cost, f"우주선 강화 시도 (+{self.current_level} → +{self.current_level + 1})")

        self.game_data["attempts"] = self.game_data.get("attempts", 0) + 1
        if self.point_system:
            self.point_system.update_game_stats(user_id=self.user_id, enhancement_attempts=1)

        success_rate = self._calculate_success_rate()
        is_success = random.random() * 100 < success_rate

        if is_success:
            self.current_level += 1
            self.game_data["level"] = self.current_level
            self.game_data["successes"] = self.game_data.get("successes", 0) + 1
            if self.point_system:
                self.point_system.set_enhancement_level(self.user_id, self.current_level)
                self.point_system.update_game_stats(user_id=self.user_id, enhancement_successes=1)

            next_cost = self._calculate_cost()
            return (
                "✅ 강화 성공!\n\n"
                f"현재 우주선 강화 레벨: +{self.current_level}\n"
                f"다음 강화 필요 골드: {next_cost}G\n"
                f"현재 골드: {self.get_user_points()}G\n\n"
                "💡 강화 레벨이 오르면 임무 보상이 커집니다."
            )

        self.game_data["failures"] = self.game_data.get("failures", 0) + 1
        if self.point_system:
            self.point_system.update_game_stats(user_id=self.user_id, enhancement_failures=1)

        if self.current_level > 0:
            self.current_level -= 1
            self.game_data["level"] = self.current_level
            if self.point_system:
                self.point_system.set_enhancement_level(self.user_id, self.current_level)
            return (
                "❌ 강화 단계가 한 단계 내려갔어요.\n\n"
                f"현재 우주선 강화 레벨: +{self.current_level}\n"
                f"현재 골드: {self.get_user_points()}G\n\n"
                "다시 시도해볼까요?"
            )

        return (
            "❌ 강화 실패...\n\n"
            f"현재 우주선 강화 레벨: +{self.current_level}\n"
            f"현재 골드: {self.get_user_points()}G\n\n"
            "다시 한 번 시도해보세요!"
        )

    def _sell(self) -> str:
        """강화 단계 정산"""
        if self.current_level == 0:
            return "❌ 정산할 강화 단계가 없습니다. 강화 후 정산해 주세요."

        sell_price = self._calculate_sell_price()
        sold_level = self.current_level

        if self.point_system:
            self.award_gold(sell_price, f"우주선 강화 정산 (+{sold_level})")

        self.current_level = 0
        self.game_data["level"] = 0
        if self.point_system:
            self.point_system.set_enhancement_level(self.user_id, 0)

        return (
            "💾 강화 단계를 정산했습니다!\n\n"
            f"정산한 강화 단계: +{sold_level}\n"
            f"정산 보상: {sell_price}G\n"
            f"현재 골드: {self.get_user_points()}G\n\n"
            "새로운 모듈로 다시 업그레이드해봐요!"
        )

    # ========== 활동 관련 메서드 ==========

    def _get_activity_type(self, name: str) -> Optional[ActivityType]:
        name_lower = name.lower()
        for activity in self.activities:
            if name_lower == activity.name.lower() or name_lower in activity.prompts:
                return activity
        return None

    def _calculate_activity_reward(self, activity: ActivityType) -> int:
        reward_multiplier = 1.0 + (
            self.current_level * (activity.multiplier or Config.MONSTER_HUNT_REWARD_MULTIPLIER)
        )
        base_reward = random.randint(*activity.reward_range)
        return int((activity.base_reward + base_reward) * reward_multiplier)

    def _perform_activity(self, activity_name: str) -> str:
        activity = self._get_activity_type(activity_name)
        if activity is None:
            return "❌ 해당 활동을 찾을 수 없습니다. 정찰, 탐사, 구조를 입력해 주세요."

        if activity.name == "구조":
            if not self._use_challenge_pass():
                passes = self._get_challenge_passes()
                return (
                    "❌ 구조 임무 패스가 부족합니다.\n"
                    f"보유 패스: {passes}장\n"
                    "'탐사'를 하면 패스를 얻을 수 있어요."
                )

        success_rate = self._calculate_success_rate(activity)
        pilot_name = self.explorer_profile.call_sign if self.explorer_profile else "탐사대"

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

            result_lines = [
                "✅ 활동 성공!",
                "",
                description,
                f"💰 리워드 +{reward}G (성장 레벨 +{self.current_level}, 배율 {reward_multiplier:.1f}%)",
                "",
            ]

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
            "❌ 활동이 잘 풀리지 않았어요...\n\n"
            f"{description}\n"
            "다시 시도해볼까요?"
            f"\n\n현재 성공 확률: {success_rate:.1f}%"
        )

    def _show_passes(self) -> str:
        passes = self._get_challenge_passes()
        drop_rate_percent = Config.BOSS_TICKET_DROP_RATE * 100

        return (
            "🎫 구조 임무 패스 현황\n\n"
            f"보유 패스: {passes}장\n\n"
            f"💡 '탐사'를 하면 {drop_rate_percent:.0f}% 확률로 패스를 얻을 수 있어요!"
        )

    def _get_status(self) -> str:
        cost = self._calculate_cost()
        success_rate = self._calculate_success_rate()
        sell_price = self._calculate_sell_price()
        passes = self._get_challenge_passes()

        status_lines = [
            "📊 현재 상태",
            "",
            "✨ 우주선 강화:",
            f"- 강화 레벨: +{self.current_level}",
            f"- 다음 강화 비용: {cost}G",
            f"- 강화 성공률: {success_rate:.1f}%",
            f"- 정산 예상 보상: {sell_price}G",
            "",
            "🎯 임무 정보:",
            f"- 보상 배율: {1.0 + (self.current_level * Config.MONSTER_HUNT_REWARD_MULTIPLIER):.2f}배",
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
                    f"- 기체: {self.explorer_profile.ship_class} ({self.explorer_profile.module})",
                    f"- 기질: {self.explorer_profile.temperament}",
                ]
            )

        return "\n".join(status_lines)

    def end(self) -> str:
        level = self.current_level
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

        self.is_active = False
        self.game_data.clear()

        return (
            "게임이 종료되었습니다.\n\n"
            "✨ 우주선 강화 요약:",
            f"- 최종 강화 레벨: +{level}\n"
            f"- 총 시도: {attempts}회 (성공 {successes}회 / 실패 {failures}회)\n\n"
            "🎯 임무 기록:",
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
            "✨ 우주선 강화:",
            "- 강화: '성장', 'train', '업그레이드'\n"
            "- 정산: '정산' 또는 'sell' (강화 리셋 후 보상)\n"
            "- 상태: '상태' 또는 'status'\n\n"
            "🎯 임무:",
            "- 정찰: '정찰', 'walk', 'scout', '1'\n"
            "- 탐사: '탐사', 'survey', 'play', '2' (패스 드랍 확률 {drop_rate:.0f}%)\n"
            "- 구조: '구조', 'rescue', 'challenge', '3' (패스 1장 소모)\n"
            "- 패스 확인: '패스', 'ticket'\n\n"
            "💡 강화 레벨이 높을수록 임무 보상이 커집니다."
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
