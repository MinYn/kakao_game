import hashlib
import random
from dataclasses import dataclass
from typing import Dict, Optional

from games.base_game import Game
from config import Config


@dataclass
class ActivityType:
    """펫 활동 타입 정보"""

    name: str
    base_reward: int
    reward_range: tuple
    multiplier: float | None = None
    prompts: tuple[str, ...] = ()
    success_rate: float = 80.0
    success_messages: tuple[str, ...] = ()
    fail_messages: tuple[str, ...] = ()


@dataclass
class PetProfile:
    """사용자별 고유 펫 프로필 (외부 과금 없는 로컬 생성)"""

    name: str
    species: str
    color: str
    accessory: str
    personality: str
    avatar: str

    @classmethod
    def from_user_id(cls, user_id: str) -> "PetProfile":
        seed = int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed)

        species_choices = ["버블펫", "도트냥", "픽셀토끼", "비트폭스", "루프펭귄"]
        colors = ["코랄", "블루", "그린", "퍼플", "옐로"]
        accessories = ["별안경", "리본", "마법모자", "후드", "헤드폰"]
        personalities = [
            "호기심 많은",
            "차분한",
            "장난꾸러기",
            "다정한",
            "모험심 가득한",
        ]

        species = rng.choice(species_choices)
        color = rng.choice(colors)
        accessory = rng.choice(accessories)
        personality = rng.choice(personalities)
        name = f"{color} {species}"

        avatar_rng = random.Random(seed ^ 0xABCDEF)
        eyes = avatar_rng.choice(["•‿•", "ᵔᴥᵔ", "✿ᴗ✿", "´｡• ᵕ •｡`", "^ᴗ^"])
        cheeks = avatar_rng.choice(["❀", "✦", "", "✧", "★"])
        ear = avatar_rng.choice(["/\\", "vv", "ʕʔ", "ɿɾ", "⟡⟡"])
        body = avatar_rng.choice(["( " + eyes + " )", "<" + eyes + ">", "{" + eyes + "}"])
        avatar = f"{ear}\n{cheeks}{body}{cheeks}"

        return cls(
            name=name,
            species=species,
            color=color,
            accessory=accessory,
            personality=personality,
            avatar=avatar,
        )


class AdventureGame(Game):
    """펫 돌봄 모험 게임"""

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
        self.pet_profile: Optional[PetProfile] = None

    def _init_activities(self) -> list:
        """활동 타입 초기화"""
        return [
            ActivityType(
                name="산책",
                base_reward=25,
                reward_range=(15, 40),
                multiplier=0.08,
                prompts=("산책", "walk", "n", "1"),
                success_rate=85.0,
                success_messages=(
                    "{pet}이(가) 상쾌한 공기를 마시며 기분이 좋아졌어요!",
                    "{pet}이(가) 주변을 구경하며 꼬리를 흔듭니다.",
                    "{pet}이(가) 새 친구를 만나 인사했어요!",
                ),
                fail_messages=(
                    "비가 와서 금방 돌아왔어요.",
                    "조금 겁을 먹고 집으로 돌아왔어요.",
                    "잠시 쉬고 싶어 하는 것 같아요.",
                ),
            ),
            ActivityType(
                name="놀이",
                base_reward=70,
                reward_range=(60, 110),
                multiplier=0.12,
                prompts=("놀이", "play", "s", "2", "특별놀이"),
                success_rate=78.0,
                success_messages=(
                    "{pet}이(가) 장난감을 끌어안고 즐거워합니다!",
                    "{pet}이(가) 신나는 비눗방울 놀이에 푹 빠졌어요!",
                    "{pet}이(가) 음악에 맞춰 깜찍하게 춤을 춰요!",
                ),
                fail_messages=(
                    "잠깐 집중이 흐트러졌어요.",
                    "장난감이 금방 질린 것 같아요.",
                    "다시 시도하면 더 즐거워질 거예요!",
                ),
            ),
            ActivityType(
                name="챌린지",
                base_reward=180,
                reward_range=(150, 260),
                multiplier=0.15,
                prompts=("챌린지", "challenge", "boss", "b", "3"),
                success_rate=65.0,
                success_messages=(
                    "{pet}이(가) 집중해서 대형 퍼즐을 완성했어요!",
                    "{pet}이(가) 새로운 재주를 성공적으로 선보였습니다!",
                    "{pet}이(가) 깜짝 미션을 멋지게 수행했어요!",
                ),
                fail_messages=(
                    "아직 조금 어려웠나 봐요.",
                    "휴식 후 다시 도전해봐요!",
                    "응원이 필요합니다. 한 번 더!",
                ),
            ),
        ]

    def _load_stats(self) -> Dict[str, int]:
        if self.point_system:
            stats = self.point_system.get_game_stats(self.user_id)
            return {
                "level": self.point_system.get_enhancement_level(self.user_id),
                "activity_count": stats.get("total_hunts", 0),
                "total_reward": stats.get("total_hunt_reward", 0),
                "activity_stats": {
                    "산책": stats.get("hunt_normal", 0),
                    "놀이": stats.get("hunt_special", 0),
                    "챌린지": stats.get("hunt_boss", 0),
                },
                "attempts": stats.get("enhancement_attempts", 0),
                "successes": stats.get("enhancement_successes", 0),
                "failures": stats.get("enhancement_failures", 0),
            }

        return {
            "level": 0,
            "activity_count": 0,
            "total_reward": 0,
            "activity_stats": {"산책": 0, "놀이": 0, "챌린지": 0},
            "attempts": 0,
            "successes": 0,
            "failures": 0,
        }

    def start(self) -> str:
        """게임 시작"""
        self.is_active = True
        self.pet_profile = PetProfile.from_user_id(self.user_id)
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
        pet_card = (
            f"{self.pet_profile.avatar}\n"
            f"이름: {self.pet_profile.name}\n"
            f"성격: {self.pet_profile.personality}\n"
            f"포인트: {self.pet_profile.color}, {self.pet_profile.accessory}"
        )

        return (
            "🐾 펫 모험을 시작합니다!\n\n"
            f"{pet_card}\n\n"
            f"현재 성장 레벨: +{self.current_level}\n"
            f"챌린지 패스: {challenge_passes}장\n\n"
            "명령어:\n"
            "✨ 성장: '성장'/'train' (골드 사용)\n"
            "💾 추억정산: '정산'/'sell' (현재 성장 단계 초기화 후 보상)\n"
            "📊 상태보기: '상태'/'status'\n\n"
            "🎯 활동:\n"
            "- '산책'/'walk': 기본 케어\n"
            "- '놀이'/'play': 특별 케어 (챌린지 패스 드랍 가능)\n"
            "- '챌린지'/'challenge': 패스를 사용해 대형 미션\n"
            "- '패스'/'ticket': 보유 챌린지 패스 확인"
        )

    def process_command(self, command: str) -> str:
        """명령 처리"""
        if not self.is_active:
            return "게임이 시작되지 않았습니다. '게임시작 모험'을 입력하세요."

        command = command.strip().lower()

        if command in ["종료", "quit", "exit"]:
            return self.end()

        if command in ["상태", "status", "info"]:
            return self._get_status()

        if command in ["성장", "train", "강화"]:
            return self._enhance()

        if command in ["정산", "sell", "추억", "돌아보기"]:
            return self._sell()

        if command in ["패스", "ticket", "tickets", "t"]:
            return self._show_passes()

        if command in ["산책", "walk", "n", "1"]:
            return self._perform_activity("산책")

        if command in ["놀이", "play", "s", "2", "특별놀이"]:
            return self._perform_activity("놀이")

        if command in ["챌린지", "challenge", "boss", "b", "3"]:
            return self._perform_activity("챌린지")

        return (
            "알 수 없는 명령입니다.\n"
            "사용 가능한 명령: 성장, 정산, 산책, 놀이, 챌린지, 패스, 상태, 종료"
        )

    # ========== 성장 관련 메서드 ==========

    def _calculate_cost(self) -> int:
        """성장 비용 계산"""
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
        """추억 정산 금액 계산"""
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
        """펫 성장"""
        cost = self._calculate_cost()

        if not self.point_system or not self.point_system.has_gold(self.user_id, cost):
            return (
                "❌ 성장을 위해 필요한 골드가 부족합니다.\n"
                f"필요 골드: {cost}G\n현재 골드: {self.get_user_points()}G"
            )

        self.deduct_gold(cost, f"펫 성장 시도 (+{self.current_level} → +{self.current_level + 1})")

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
                "✅ 성장 성공!\n\n"
                f"현재 성장 레벨: +{self.current_level}\n"
                f"다음 성장 필요 골드: {next_cost}G\n"
                f"현재 골드: {self.get_user_points()}G\n\n"
                "💡 성장 레벨이 오르면 활동 보상이 커집니다."
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
                "❌ 성장 단계가 한 단계 내려갔어요.\n\n"
                f"현재 성장 레벨: +{self.current_level}\n"
                f"현재 골드: {self.get_user_points()}G\n\n"
                "다시 시도해볼까요?"
            )

        return (
            "❌ 성장 실패...\n\n"
            f"현재 성장 레벨: +{self.current_level}\n"
            f"현재 골드: {self.get_user_points()}G\n\n"
            "다시 한 번 시도해보세요!"
        )

    def _sell(self) -> str:
        """성장 단계 정산"""
        if self.current_level == 0:
            return "❌ 정산할 성장이 없습니다. 성장 후 정산해 주세요."

        sell_price = self._calculate_sell_price()
        sold_level = self.current_level

        if self.point_system:
            self.award_gold(sell_price, f"펫 성장 정산 (+{sold_level})")

        self.current_level = 0
        self.game_data["level"] = 0
        if self.point_system:
            self.point_system.set_enhancement_level(self.user_id, 0)

        return (
            "💾 추억을 정산했습니다!\n\n"
            f"정산한 성장 단계: +{sold_level}\n"
            f"정산 보상: {sell_price}G\n"
            f"현재 골드: {self.get_user_points()}G\n\n"
            "새로운 목표로 다시 키워봐요!"
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
            return "❌ 해당 활동을 찾을 수 없습니다. 산책, 놀이, 챌린지를 입력해 주세요."

        if activity.name == "챌린지":
            if not self._use_challenge_pass():
                passes = self._get_challenge_passes()
                return (
                    "❌ 챌린지 패스가 부족합니다.\n"
                    f"보유 패스: {passes}장\n"
                    "'놀이'를 하면 패스를 얻을 수 있어요."
                )

        success_rate = self._calculate_success_rate(activity)
        pet_name = self.pet_profile.name if self.pet_profile else "펫"

        if random.random() * 100 < success_rate:
            reward = self._calculate_activity_reward(activity)
            if self.point_system:
                self.award_gold(reward, f"{activity.name} 성공 ({pet_name})")

            self.activity_count += 1
            self.total_reward += reward
            self.activity_stats[activity.name] = self.activity_stats.get(activity.name, 0) + 1
            self.game_data["activity_count"] = self.activity_count
            self.game_data["total_reward"] = self.total_reward
            self.game_data["activity_stats"] = self.activity_stats

            if self.point_system:
                activity_map = {"산책": "hunt_normal", "놀이": "hunt_special", "챌린지": "hunt_boss"}
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
            description = random.choice(activity.success_messages).format(pet=pet_name)

            result_lines = [
                "✅ 활동 성공!",
                "",
                description,
                f"💰 리워드 +{reward}G (성장 레벨 +{self.current_level}, 배율 {reward_multiplier:.1f}%)",
                "",
            ]

            if activity.name == "놀이":
                if random.random() < Config.BOSS_TICKET_DROP_RATE:
                    new_passes = self._add_challenge_pass()
                    result_lines.append(f"🎫 챌린지 패스 획득! (현재: {new_passes}장)")
                    result_lines.append("")

            result_lines.extend(
                [
                    "활동 통계:",
                    f"- 산책: {self.activity_stats.get('산책', 0)}회",
                    f"- 놀이: {self.activity_stats.get('놀이', 0)}회",
                    f"- 챌린지: {self.activity_stats.get('챌린지', 0)}회",
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
            "🎫 챌린지 패스 현황\n\n"
            f"보유 패스: {passes}장\n\n"
            f"💡 '놀이'를 하면 {drop_rate_percent:.0f}% 확률로 패스를 얻을 수 있어요!"
        )

    def _get_status(self) -> str:
        cost = self._calculate_cost()
        success_rate = self._calculate_success_rate()
        sell_price = self._calculate_sell_price()
        passes = self._get_challenge_passes()

        status_lines = [
            "📊 현재 상태",
            "",
            "✨ 성장 정보:",
            f"- 성장 레벨: +{self.current_level}",
            f"- 다음 성장 비용: {cost}G",
            f"- 성장 성공률: {success_rate:.1f}%",
            f"- 정산 예상 보상: {sell_price}G",
            "",
            "🎯 활동 정보:",
            f"- 보상 배율: {1.0 + (self.current_level * Config.MONSTER_HUNT_REWARD_MULTIPLIER):.2f}배",
            f"- 챌린지 패스: {passes}장",
            "",
            "📈 통계:",
            f"- 성장 시도: {self.game_data.get('attempts', 0)}회",
            f"- 성장 성공: {self.game_data.get('successes', 0)}회",
            f"- 성장 실패: {self.game_data.get('failures', 0)}회",
            f"- 산책: {self.activity_stats.get('산책', 0)}회",
            f"- 놀이: {self.activity_stats.get('놀이', 0)}회",
            f"- 챌린지: {self.activity_stats.get('챌린지', 0)}회",
            f"- 총 활동: {self.activity_count}회",
            f"- 총 획득 골드: {self.total_reward}G",
            f"- 현재 골드: {self.get_user_points()}G",
        ]

        if self.pet_profile:
            status_lines.extend(
                [
                    "",
                    "🐾 펫 프로필:",
                    f"- 이름: {self.pet_profile.name}",
                    f"- 성격: {self.pet_profile.personality}",
                    f"- 포인트: {self.pet_profile.color}, {self.pet_profile.accessory}",
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
                hunt_normal=stats.get("산책", 0),
                hunt_special=stats.get("놀이", 0),
                hunt_boss=stats.get("챌린지", 0),
                total_hunts=activity_count,
                total_hunt_reward=reward,
            )

        self.is_active = False
        self.game_data.clear()

        return (
            "게임이 종료되었습니다.\n\n"
            "✨ 성장:",
            f"- 최종 성장 레벨: +{level}\n"
            f"- 총 시도: {attempts}회 (성공 {successes}회 / 실패 {failures}회)\n\n"
            "🎯 활동:",
            f"- 산책: {stats.get('산책', 0)}회\n"
            f"- 놀이: {stats.get('놀이', 0)}회\n"
            f"- 챌린지: {stats.get('챌린지', 0)}회\n"
            f"- 총 활동: {activity_count}회\n"
            f"- 총 획득 골드: {reward}G"
        )

    def get_help(self) -> str:
        drop_rate = Config.BOSS_TICKET_DROP_RATE * 100
        return (
            "펫 모험 도움말:\n\n"
            "✨ 성장:",
            "- 성장: '성장' 또는 'train'\n"
            "- 정산: '정산' 또는 'sell' (성장 리셋 후 보상)\n"
            "- 상태: '상태' 또는 'status'\n\n"
            "🎯 활동:",
            "- 산책: '산책', 'walk', '1'\n"
            "- 놀이: '놀이', 'play', '2' (패스 드랍 확률 {drop_rate:.0f}%)\n"
            "- 챌린지: '챌린지', 'challenge', '3' (패스 1장 소모)\n"
            "- 패스 확인: '패스', 'ticket'\n\n"
            "💡 성장 레벨이 높을수록 활동 보상이 커집니다."
        )

    # ========== 패스 관련 유틸리티 ==========

    def _get_challenge_passes(self) -> int:
        if not self.point_system:
            return 0
        return self.point_system.get_boss_tickets(self.user_id)

    def _add_challenge_pass(self, amount: int = 1) -> int:
        if not self.point_system:
            return amount
        return self.point_system.add_boss_ticket(self.user_id, amount, "챌린지 패스 획득")

    def _use_challenge_pass(self, amount: int = 1) -> bool:
        if not self.point_system:
            return True
        return self.point_system.use_boss_ticket(self.user_id, amount, "챌린지 진행")
