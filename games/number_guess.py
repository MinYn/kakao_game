import random
from games.base_game import Game
from config import Config


class NumberGuessGame(Game):
    """숫자 맞추기 게임"""

    def __init__(self, user_id: str, min_num: int = 1,
                 max_num: int = 100, point_system=None):
        super().__init__(user_id, point_system)
        self.min_num = min_num
        self.max_num = max_num
        self.target_number = None
        self.attempts = 0
        self.max_attempts = 10
        self.entry_cost = Config.NUMBER_GUESS_ENTRY_COST
        self.base_reward = Config.NUMBER_GUESS_BASE_REWARD
        self.bonus_per_attempt = Config.NUMBER_GUESS_BONUS_PER_ATTEMPT
        self.consolation = Config.NUMBER_GUESS_CONSOLATION

    def start(self) -> str:
        """게임 시작"""
        if (self.point_system and
                not self.point_system.has_gold(self.user_id,
                                                 self.entry_cost)):
            return (f"❌ 게임을 시작하려면 {self.entry_cost}골드가 "
                    f"필요합니다.\n현재 골드: {self.get_user_points()}G\n"
                    f"'골드' 명령어로 골드를 확인하세요.")

        if self.point_system:
            self.deduct_gold(self.entry_cost, "숫자맞추기 게임 입장료")

        self.is_active = True
        self.target_number = random.randint(self.min_num, self.max_num)
        self.attempts = 0
        self.game_data = {
            'target': self.target_number,
            'attempts': 0,
            'min': self.min_num,
            'max': self.max_num,
            'entry_cost': self.entry_cost
        }
        return (f"🎮 숫자 맞추기 게임 시작! (입장료: {self.entry_cost}G)\n"
                f"{self.min_num}부터 {self.max_num}까지의 숫자를 맞춰보세요.\n"
                f"최대 {self.max_attempts}번의 기회가 있습니다.")

    def process_command(self, command: str) -> str:
        """명령 처리"""
        if not self.is_active:
            return "게임이 시작되지 않았습니다. '시작' 명령을 사용하세요."

        command = command.strip()

        # 숫자 파싱
        try:
            guess = int(command)
        except ValueError:
            if command.lower() in ['포기', '종료', 'quit', 'exit']:
                return self.end()
            return (
                f"숫자를 입력해주세요. "
                f"(현재 범위: {self.min_num}~{self.max_num})"
            )

        self.attempts += 1
        self.game_data['attempts'] = self.attempts

        if guess < self.min_num or guess > self.max_num:
            return (f"범위를 벗어났습니다. "
                    f"{self.min_num}~{self.max_num} 사이의 숫자를 입력하세요.")

        if guess == self.target_number:
            # 골드 지급 (시도 횟수에 따라 차등 지급)
            bonus = max(
                0,
                (self.max_attempts - self.attempts) * self.bonus_per_attempt
            )
            total_reward = self.base_reward + bonus

            if self.point_system:
                self.award_gold(
                    total_reward,
                    f"숫자맞추기 게임 클리어 ({self.attempts}번 시도)"
                )

            result = (
                f"🎉 정답입니다! {self.attempts}번 만에 맞췄어요!\n"
                f"💰 골드 +{total_reward}G 획득!"
            )
            self.end()
            return result

        if self.attempts >= self.max_attempts:
            # 실패 시 작은 보상 (참여 골드)
            if self.point_system:
                self.award_gold(self.consolation,
                                  "숫자맞추기 게임 참여 보상")
            result = (f"😢 기회를 모두 사용했습니다. "
                      f"정답은 {self.target_number}였습니다.\n"
                      f"💰 참여 보상 +{self.consolation}G")
            self.end()
            return result

        if guess < self.target_number:
            hint = "⬆️ 더 큰 숫자입니다."
        else:
            hint = "⬇️ 더 작은 숫자입니다."
        remaining = self.max_attempts - self.attempts
        return f"{hint}\n남은 기회: {remaining}번"

    def get_help(self) -> str:
        """도움말"""
        return """숫자 맞추기 게임 도움말:
- 게임 시작: '시작' 또는 '게임시작'
- 숫자 입력: 1~100 사이의 숫자
- 게임 종료: '포기', '종료'
- 목표: 최소한의 시도로 정답을 맞추세요!"""
