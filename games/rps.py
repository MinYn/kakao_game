import random
from games.base_game import Game
from config import Config


class RockPaperScissorsGame(Game):
    """가위바위보 게임"""
    
    def __init__(self, user_id: str, point_system=None):
        super().__init__(user_id, point_system)
        self.choices = ['가위', '바위', '보']
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.win_reward = Config.RPS_WIN_REWARD
        self.lose_cost = Config.RPS_LOSE_COST
    
    def start(self) -> str:
        """게임 시작"""
        self.is_active = True
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.game_data = {
            'wins': 0,
            'losses': 0,
            'draws': 0
        }
        return "🎮 가위바위보 게임 시작!\n'가위', '바위', '보' 중 하나를 입력하세요.\n승리 시 +10G, 패배 시 -5G\n'종료'를 입력하면 게임이 끝납니다."
    
    def process_command(self, command: str) -> str:
        """명령 처리"""
        if not self.is_active:
            return "게임이 시작되지 않았습니다. '시작' 명령을 사용하세요."
        
        command = command.strip()
        
        if command.lower() in ['종료', 'quit', 'exit']:
            return self.end()
        
        # 입력 정규화
        user_choice = None
        for choice in self.choices:
            if choice in command or command.lower() in ['가위', '바위', '보', 'scissors', 'rock', 'paper']:
                if '가위' in command or command.lower() == 'scissors':
                    user_choice = '가위'
                elif '바위' in command or command.lower() == 'rock':
                    user_choice = '바위'
                elif '보' in command or command.lower() == 'paper':
                    user_choice = '보'
                break
        
        if user_choice is None:
            return "가위, 바위, 보 중 하나를 입력해주세요."
        
        # 컴퓨터 선택
        computer_choice = random.choice(self.choices)
        
        # 승부 판정
        result = self._judge(user_choice, computer_choice)
        
        point_msg = ""
        if result == 'win':
            self.wins += 1
            self.game_data['wins'] = self.wins
            result_msg = "🎉 승리!"
            # 승리 시 골드 지급
            if self.point_system:
                self.award_gold(self.win_reward, "가위바위보 게임 승리")
                point_msg = f"\n💰 +{self.win_reward}G 획득!"
        elif result == 'lose':
            self.losses += 1
            self.game_data['losses'] = self.losses
            result_msg = "😢 패배..."
            # 패배 시 골드 차감
            if self.point_system:
                deducted = self.deduct_gold(self.lose_cost, "가위바위보 게임 패배")
                if deducted is not None:
                    point_msg = f"\n💸 -{self.lose_cost}G 차감"
                else:
                    point_msg = f"\n⚠️ 골드 부족으로 차감되지 않았습니다."
        else:
            self.draws += 1
            self.game_data['draws'] = self.draws
            result_msg = "🤝 무승부"
        
        stats = f"\n전적: {self.wins}승 {self.losses}패 {self.draws}무"
        return f"당신: {user_choice} vs 컴퓨터: {computer_choice}\n{result_msg}{point_msg}{stats}"
    
    def _judge(self, user: str, computer: str) -> str:
        """승부 판정"""
        if user == computer:
            return 'draw'
        
        win_conditions = {
            '가위': '보',
            '바위': '가위',
            '보': '바위'
        }
        
        if win_conditions[user] == computer:
            return 'win'
        return 'lose'
    
    def get_help(self) -> str:
        """도움말"""
        return """가위바위보 게임 도움말:
- 게임 시작: '시작' 또는 '게임시작'
- 입력: '가위', '바위', '보'
- 게임 종료: '종료'
- 목표: 컴퓨터를 이겨보세요!"""

