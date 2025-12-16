from typing import Dict, Optional
from games.base_game import Game
from games.number_guess import NumberGuessGame
from games.rps import RockPaperScissorsGame
from games.adventure import AdventureGame
from point_system import PointSystem
from config import Config


class GameEngine:
    """게임 엔진 - 게임 관리 및 명령 처리"""
    
    def __init__(self, point_system: Optional[PointSystem] = None):
        self.active_games: Dict[str, Game] = {}
        self.point_system = point_system or PointSystem()
        self.available_games = {
            '숫자맞추기': NumberGuessGame,
            'number': NumberGuessGame,
            '가위바위보': RockPaperScissorsGame,
            'rps': RockPaperScissorsGame,
            '모험': AdventureGame,
            'adventure': AdventureGame,
            'adv': AdventureGame,
        }
    
    def process_message(self, user_id: str, message: str) -> str:
        """사용자 메시지 처리"""
        # 신규 사용자 초기 골드 지급
        is_new_user = self.point_system.ensure_initial_points(user_id)
        
        message = message.strip()
        
        # 골드 조회 (단축키: g, gold, p, pt)
        if message.lower() in ['골드', 'gold', 'g', '포인트', 'point', 'points', '잔액', '내골드', 'p', 'pt']:
            response = self._get_points(user_id)
            if is_new_user:
                response = f"🎉 환영합니다! 신규 사용자에게 {Config.INITIAL_POINTS}G를 지급했습니다!\n\n{response}"
            return response
        
        # 골드 전송 (단축키: pay, send)
        msg_lower = message.lower()
        if (msg_lower.startswith('골드주기') or msg_lower.startswith('골드전송') or
            msg_lower.startswith('pay ') or msg_lower.startswith('send ')):
            # 단축키 변환
            if msg_lower.startswith('pay '):
                message = '골드주기 ' + message[4:]
            elif msg_lower.startswith('send '):
                message = '골드주기 ' + message[5:]
            return self._transfer_points(user_id, message)
        
        # 리더보드 (단축키: l, lb, rank)
        if message.lower() in ['리더보드', '랭킹', 'leaderboard', 'ranking', 'l', 'lb', 'rank', 'r']:
            return self._get_leaderboard()
        
        # 게임 목록 (단축키: g, gl, list)
        if message.lower() in ['게임목록', '게임', 'games', 'list', 'g', 'gl']:
            return self._list_games()
        
        # 도움말 (단축키: h, ?)
        if message.lower() in ['도움말', 'help', '?', 'h']:
            return self._get_help()
        
        # 게임 시작 (단축키: s, start, gs)
        msg_lower = message.lower()
        if (msg_lower.startswith('게임시작') or msg_lower.startswith('시작') or 
            msg_lower.startswith('s ') or msg_lower.startswith('start ') or 
            msg_lower.startswith('gs ')):
            # 단축키 변환
            if msg_lower.startswith('s '):
                game_name = message[2:].strip()
            elif msg_lower.startswith('start '):
                game_name = message[6:].strip()
            elif msg_lower.startswith('gs '):
                game_name = message[3:].strip()
            else:
                game_name = message.replace('게임시작', '').replace('시작', '').strip()
            return self._start_game(user_id, game_name)
        
        # 게임 종료 (단축키: e, end, ge)
        if message.lower() in ['게임종료', '종료', 'end', 'e', 'ge']:
            return self._end_game(user_id)
        
        # 활성 게임이 있으면 게임 명령 처리
        if user_id in self.active_games:
            game = self.active_games[user_id]
            if game.is_game_active():
                return game.process_command(message)
        
        # 기본 응답
        return "게임을 시작하려면 '게임시작 [게임이름]' 또는 's [게임]'을 입력하세요.\n'게임목록' 또는 'g'로 사용 가능한 게임을 확인할 수 있습니다."
    
    def _list_games(self) -> str:
        """게임 목록 반환"""
        games_list = [
            "🎮 사용 가능한 게임:",
            "1. 숫자맞추기 (number, n, 1) - 1~100 사이의 숫자를 맞춰보세요",
            "2. 가위바위보 (rps, r, 2) - 컴퓨터와 가위바위보를 해보세요",
            "3. 모험 (adventure, a, adv, 3) - 강화와 몬스터 사냥을 한 게임에서!",
            "",
            "사용법: '게임시작 [게임이름]' 또는 's [게임]'"
        ]
        return "\n".join(games_list)
    
    def _get_help(self) -> str:
        """도움말 반환"""
        help_text = [
            "🎮 게임 봇 도움말",
            "",
            "명령어 (단축키):",
            "- 골드 (g, gold, p, pt): 내 골드 조회",
            "- 골드주기 [사용자] [금액] (pay, send): 다른 사용자에게 골드 전송",
            "- 리더보드 (l, lb, rank): 골드 랭킹 보기",
            "- 게임목록 (g, gl): 사용 가능한 게임 목록 보기",
            "- 게임시작 [게임이름] (s, start, gs): 게임 시작",
            "  게임 단축키: 숫자맞추기(n, 1), 가위바위보(r, 2), 모험(a, adv, 3)",
            "- 게임종료 (e, end, ge): 현재 게임 종료",
            "- 도움말 (h, ?): 이 도움말 보기",
            "",
            "게임 중에는 게임 명령을 입력하세요."
        ]
        return "\n".join(help_text)
    
    def _get_enhancement_level(self, user_id: str) -> int:
        """사용자의 현재 강화 레벨 조회 (AdventureGame에서)"""
        if user_id in self.active_games:
            game = self.active_games[user_id]
            if isinstance(game, AdventureGame) and game.is_game_active():
                return game.current_level
        
        # 활성 모험 게임이 없으면 0 반환
        return 0
    
    def _start_game(self, user_id: str, game_name: str) -> str:
        """게임 시작"""
        # 기존 게임 종료
        if user_id in self.active_games:
            self.active_games[user_id].end()
        
        # 게임 이름 정규화
        game_name = game_name.lower() if game_name else ''
        
        # 게임 단축키 매핑
        game_shortcuts = {
            'n': 'number',
            'num': 'number',
            '1': 'number',
            'r': 'rps',
            '2': 'rps',
            'a': 'adventure',
            'adv': 'adventure',
            '3': 'adventure',
        }
        
        # 단축키 변환
        if game_name in game_shortcuts:
            game_name = game_shortcuts[game_name]
        
        # 게임 찾기
        game_class = None
        for key, cls in self.available_games.items():
            if key.lower() == game_name or game_name in key.lower():
                game_class = cls
                break
        
        if game_class is None:
            return f"'{game_name}' 게임을 찾을 수 없습니다.\n'게임목록' 또는 'g'로 사용 가능한 게임을 확인하세요."
        
        # 게임 생성 및 시작
        try:
            game = game_class(user_id, point_system=self.point_system)
            self.active_games[user_id] = game
            return game.start()
        except Exception as e:
            return f"게임 시작 중 오류가 발생했습니다: {str(e)}"
    
    def _end_game(self, user_id: str) -> str:
        """게임 종료"""
        if user_id not in self.active_games:
            return "진행 중인 게임이 없습니다."
        
        game = self.active_games[user_id]
        result = game.end()
        del self.active_games[user_id]
        return result
    
    def has_active_game(self, user_id: str) -> bool:
        """사용자가 활성 게임을 가지고 있는지 확인"""
        return user_id in self.active_games and self.active_games[user_id].is_game_active()
    
    def _get_points(self, user_id: str) -> str:
        """골드 조회"""
        points = self.point_system.get_points(user_id)
        return f"💰 현재 골드: {points}G"
    
    def _transfer_points(self, from_user: str, message: str) -> str:
        """골드 전송 처리"""
        # 명령 파싱: "골드주기 [사용자] [금액]" 또는 "골드주기 [금액] [사용자]"
        parts = message.replace('골드주기', '').replace('골드전송', '').strip().split()
        
        if len(parts) < 2:
            return "❌ 사용법: '골드주기 [사용자] [금액]'\n예: 골드주기 alice 50"
        
        # 금액과 사용자 추출
        to_user = None
        amount = None
        
        for part in parts:
            # 숫자인지 확인
            try:
                amount = int(part)
            except ValueError:
                # 숫자가 아니면 사용자 이름
                to_user = part
        
        if to_user is None or amount is None:
            return "❌ 사용법: '골드주기 [사용자] [금액]'\n예: 골드주기 alice 50"
        
        if amount <= 0:
            return "❌ 전송할 골드는 1G 이상이어야 합니다."
        
        # 자기 자신에게 전송 불가
        if from_user == to_user:
            return "❌ 자기 자신에게 골드를 전송할 수 없습니다."
        
        # 골드 확인
        current_points = self.point_system.get_points(from_user)
        if current_points < amount:
            return f"❌ 골드가 부족합니다.\n현재 골드: {current_points}G\n전송하려는 골드: {amount}G"
        
        # 골드 전송
        result = self.point_system.transfer_points(
            from_user, 
            to_user, 
            amount, 
            "사용자 간 골드 전송"
        )
        
        if result is None:
            return "❌ 골드 전송에 실패했습니다."
        
        return f"""✅ 골드 전송 완료!

보낸 사람: {from_user}
받은 사람: {to_user}
전송 금액: {amount}G

{from_user}의 남은 골드: {self.point_system.get_points(from_user)}G
{to_user}의 현재 골드: {result}G"""
    
    def _get_leaderboard(self, limit: int = 10) -> str:
        """리더보드 조회"""
        leaderboard = self.point_system.get_leaderboard(limit)
        
        if not leaderboard:
            return "📊 아직 랭킹 데이터가 없습니다."
        
        result = ["🏆 골드 리더보드", ""]
        for idx, (user_id, points) in enumerate(leaderboard, 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            result.append(f"{medal} {user_id}: {points}G")
        
        return "\n".join(result)

