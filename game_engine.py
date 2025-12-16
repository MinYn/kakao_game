from typing import Dict, Optional, List, Tuple, Any
from games.base_game import Game
from games.number_guess import NumberGuessGame
from games.rps import RockPaperScissorsGame
from games.adventure import AdventureGame
from gold_system import GoldSystem
from config import Config


class GameEngine:
    """게임 엔진 - 게임 관리 및 명령 처리"""
    
    def __init__(self, gold_system: Optional[GoldSystem] = None):
        self.active_games: Dict[str, Game] = {}
        self.gold_system = gold_system or GoldSystem()
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
        is_new_user = self.gold_system.ensure_initial_gold(user_id)
        
        message = message.strip()

        # 커맨드 형태 처리 (/명령어 또는 @봇이름 명령어)
        # "/골드" 또는 "@게임봇 골드" 형태 지원
        if message.startswith('/'):
            # 슬래시 커맨드: "/골드" -> "골드"
            message = message[1:].strip()
        elif message.startswith('@'):
            # @봇이름 커맨드: "@게임봇 골드" -> "골드"
            # @ 뒤의 공백까지 제거
            parts = message[1:].split(None, 1)  # 최대 1번만 분할
            if len(parts) > 1:
                # 봇 이름 뒤의 명령어만 추출
                message = parts[1].strip()
            else:
                message = ''  # "@봇이름"만 입력한 경우
        
        # 골드 조회 (단축키: g, gold, p, pt)
        gold_commands = [
            '골드', 'gold', 'g', '포인트', 'point', 'points',
            '잔액', '내골드', 'p', 'pt'
        ]
        if message.lower() in gold_commands:
            response = self._get_gold(user_id)
            if is_new_user:
                response = (
                    f"🎉 환영합니다! 신규 사용자에게 "
                    f"{Config.INITIAL_GOLD}G를 지급했습니다!\n\n"
                    f"{response}"
                )
            return response
        
        # 골드 전송 (단축키: pay, send)
        msg_lower = message.lower()
        if (msg_lower.startswith('골드주기') or
                msg_lower.startswith('골드전송') or
                msg_lower.startswith('pay ') or
                msg_lower.startswith('send ')):
            # 단축키 변환
            if msg_lower.startswith('pay '):
                message = '골드주기 ' + message[4:]
            elif msg_lower.startswith('send '):
                message = '골드주기 ' + message[5:]
            return self._transfer_gold(user_id, message)
        
        # 리더보드 (단축키: l, lb, rank)
        leaderboard_commands = [
            '리더보드', '랭킹', 'leaderboard', 'ranking',
            'l', 'lb', 'rank', 'r'
        ]
        if message.lower() in leaderboard_commands:
            return self._get_leaderboard()
        
        # 게임 목록 (단축키: g, gl, list)
        game_list_commands = [
            '게임목록', '게임', 'games', 'list', 'g', 'gl'
        ]
        if message.lower() in game_list_commands:
            return self._list_games()
        
        # 도움말 (단축키: h, ?)
        if message.lower() in ['도움말', 'help', '?', 'h']:
            return self._get_help()
        
        # 게임 시작 (단축키: s, start, gs)
        msg_lower = message.lower()
        if (msg_lower.startswith('게임시작') or
                msg_lower.startswith('시작') or
                msg_lower.startswith('s ') or
                msg_lower.startswith('start ') or
                msg_lower.startswith('gs ')):
            # 단축키 변환
            if msg_lower.startswith('s '):
                game_name = message[2:].strip()
            elif msg_lower.startswith('start '):
                game_name = message[6:].strip()
            elif msg_lower.startswith('gs '):
                game_name = message[3:].strip()
            else:
                game_name = (
                    message.replace('게임시작', '')
                    .replace('시작', '')
                    .strip()
                )
            return self._start_game(user_id, game_name)

        # 게임 종료 (단축키: e, end, ge)
        end_commands = ['게임종료', '종료', 'end', 'e', 'ge']
        if message.lower() in end_commands:
            return self._end_game(user_id)
        
        # 활성 게임이 있으면 게임 명령 처리
        if user_id in self.active_games:
            game = self.active_games[user_id]
            if game.is_game_active():
                return game.process_command(message)
        
        # 기본 응답
        return (
            "게임을 시작하려면 '게임시작 [게임이름]' 또는 "
            "'s [게임]'을 입력하세요.\n"
            "'게임목록' 또는 'g'로 사용 가능한 게임을 확인할 수 있습니다."
        )
    
    def _list_games(self) -> str:
        """게임 목록 반환"""
        games_list = [
            "🎮 사용 가능한 게임:",
            "1. 숫자맞추기 (number, n, 1) - 1~100 사이의 숫자를 맞춰보세요",
            "2. 가위바위보 (rps, r, 2) - 컴퓨터와 가위바위보를 해보세요",
            "3. 모험 (adventure, a, adv, 3) - 강화와 몬스터 사냥을 한 게임에서!",
            "",
            "사용법: '게임시작 [게임이름]' 또는 's [게임]'",
            "",
            "커맨드 형태도 지원: '/게임시작 모험', '@게임봇 게임시작 모험'"
        ]
        return "\n".join(games_list)
    
    def _get_help(self) -> str:
        """도움말 반환"""
        help_text = [
            "🎮 게임 봇 도움말",
            "",
            "명령어 사용법:",
            "- 일반 명령어: '골드', '게임시작 모험' 등",
            "- 슬래시 커맨드: '/골드', '/게임시작 모험' 등",
            "- @봇이름 커맨드: '@게임봇 골드', "
            "'@게임봇 게임시작 모험' 등",
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
            "예시:",
            "- /골드",
            "- /게임시작 모험",
            "- @게임봇 리더보드",
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
            return (
                f"'{game_name}' 게임을 찾을 수 없습니다.\n"
                "'게임목록' 또는 'g'로 사용 가능한 게임을 확인하세요."
            )
        
        # 게임 생성 및 시작
        try:
            game = game_class(
                user_id, point_system=self.gold_system
            )
            self.active_games[user_id] = game
            return game.start()
        except (ValueError, AttributeError, KeyError) as e:
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
    
    def _get_gold(self, user_id: str) -> str:
        """골드 조회"""
        gold = self.gold_system.get_gold(user_id)
        return f"💰 현재 골드: {gold}G"
    
    def _transfer_gold(self, from_user: str, message: str) -> str:
        """골드 전송 처리"""
        # 명령 파싱: "골드주기 [사용자] [금액]" 또는 "골드주기 [금액] [사용자]"
        parts = message.replace('골드주기', '').replace('골드전송', '').strip().split()
        
        if len(parts) < 2:
            return (
                "❌ 사용법: '골드주기 [사용자] [금액]'\n"
                "예: 골드주기 alice 50"
            )
        
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
        current_gold = self.gold_system.get_gold(from_user)
        if current_gold < amount:
            return (
                f"❌ 골드가 부족합니다.\n"
                f"현재 골드: {current_gold}G\n"
                f"전송하려는 골드: {amount}G"
            )
        
        # 골드 전송
        result = self.gold_system.transfer_gold(
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

{from_user}의 남은 골드: {self.gold_system.get_gold(from_user)}G
{to_user}의 현재 골드: {result}G"""
    
    def _get_leaderboard(self, limit: int = 10) -> str:
        """리더보드 조회"""
        leaderboard = self.gold_system.get_leaderboard(limit)
        
        if not leaderboard:
            return "📊 아직 랭킹 데이터가 없습니다."
        
        result = ["🏆 골드 리더보드", ""]
        for idx, (user_id, gold) in enumerate(leaderboard, 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            result.append(f"{medal} {user_id}: {gold}G")
        
        return "\n".join(result)
    
    def get_ui_buttons(self, user_id: str, response: str = None) -> List[Dict[str, str]]:
        """UI 버튼 목록 반환 (플랫폼별 UI 생성용)
        
        Args:
            user_id: 사용자 ID
            response: 응답 메시지 (선택사항, 게임 상태 판단용)
            
        Returns:
            버튼 목록 [{'label': '...', 'messageText': '...'}, ...]
        """
        # 모험 게임 중인지 확인
        is_adventure = self.has_active_game(user_id)
        
        if is_adventure:
            # 응답 텍스트로 모험 게임인지 확인
            if response and ('강화' in response or '일반몹' in response or 
                           '특수몹' in response or '보스몹' in response or '모험' in response):
                return [
                    {'label': '🔨 강화', 'messageText': '강화'},
                    {'label': '🗡️ 사냥', 'messageText': '사냥'},
                    {'label': '💰 판매', 'messageText': '판매'},
                    {'label': '📊 상태', 'messageText': '상태'},
                    {'label': '🏠 홈', 'messageText': '게임종료'},
                ]
            else:
                return [
                    {'label': '💰 골드', 'messageText': '골드'},
                    {'label': '🎮 게임시작', 'messageText': '게임시작 모험'},
                    {'label': '🏆 랭킹', 'messageText': '리더보드'},
                    {'label': '📋 게임목록', 'messageText': '게임목록'},
                    {'label': '❓ 도움말', 'messageText': '도움말'},
                ]
        else:
            # 기본 버튼
            return [
                {'label': '💰 골드', 'messageText': '골드'},
                {'label': '🎮 게임시작', 'messageText': '게임시작 모험'},
                {'label': '🏆 랭킹', 'messageText': '리더보드'},
                {'label': '📋 게임목록', 'messageText': '게임목록'},
                {'label': '❓ 도움말', 'messageText': '도움말'},
            ]
    
    def should_generate_image(self, user_id: str, command: str, response: str) -> bool:
        """이미지 생성이 필요한지 확인
        
        Args:
            user_id: 사용자 ID
            command: 명령어
            response: 응답 메시지
            
        Returns:
            이미지 생성 필요 여부
        """
        if not response:
            return False
        
        # 강화 결과 확인
        if '강화 성공' in response or '강화 실패' in response:
            return user_id in self.active_games
        
        # 사냥 결과 확인
        if '사냥 성공' in response or '사냥 실패' in response:
            return user_id in self.active_games
        
        return False
    
    def get_enhancement_image_data(self, user_id: str, response: str) -> Optional[Dict[str, Any]]:
        """강화 이미지 생성에 필요한 데이터 반환
        
        Args:
            user_id: 사용자 ID
            response: 응답 메시지
            
        Returns:
            이미지 생성 데이터 딕셔너리 또는 None
        """
        if user_id not in self.active_games:
            return None
        
        game = self.active_games[user_id]
        if not hasattr(game, 'current_level'):
            return None
        
        # 강화 결과 파싱
        is_success = '강화 성공' in response
        level = game.current_level
        previous_level = None
        
        # 실패 시 이전 레벨 추출
        if not is_success and '→' in response:
            import re
            match = re.search(r'\+(\d+)\s*→\s*\+(\d+)', response)
            if match:
                previous_level = int(match.group(1))
                level = int(match.group(2))
        
        gold = game.get_user_points() if hasattr(game, 'get_user_points') else 0
        
        # 추가 정보 수집
        next_cost = 0
        next_success_rate = 0
        attempts = 0
        successes = 0
        failures = 0
        
        if hasattr(game, '_calculate_cost'):
            next_cost = game._calculate_cost()
        if hasattr(game, '_calculate_success_rate'):
            next_success_rate = game._calculate_success_rate()
        if hasattr(game, 'game_data'):
            attempts = game.game_data.get('attempts', 0)
            successes = game.game_data.get('successes', 0)
            failures = game.game_data.get('failures', 0)
        
        return {
            'level': level,
            'max_level': None,  # 최대 레벨 제한 없음
            'is_success': is_success,
            'previous_level': previous_level,
            'gold': gold,
            'next_cost': next_cost,
            'next_success_rate': next_success_rate,
            'attempts': attempts,
            'successes': successes,
            'failures': failures
        }
    
    def get_hunt_image_data(self, user_id: str, command: str, response: str) -> Optional[Dict[str, Any]]:
        """사냥 이미지 생성에 필요한 데이터 반환
        
        Args:
            user_id: 사용자 ID
            command: 명령어
            response: 응답 메시지
            
        Returns:
            이미지 생성 데이터 딕셔너리 또는 None
        """
        if user_id not in self.active_games:
            return None
        
        game = self.active_games[user_id]
        if not hasattr(game, 'current_level'):
            return None
        
        # 사냥 결과 파싱
        is_success = '사냥 성공' in response
        level = game.current_level
        gold = game.get_user_points() if hasattr(game, 'get_user_points') else 0
        
        # 몬스터 정보 추출
        monster_name = "몬스터"
        monster_type = "일반몹"
        reward = 0
        
        # 골드 추출
        import re
        gold_match = re.search(r'\+(\d+)G', response)
        if gold_match:
            reward = int(gold_match.group(1))
        
        # 몬스터 타입 확인 (우선순위: command > monster_names > response 메시지)
        # command가 명확한 경우 우선 사용
        if command:
            # 정확한 타입명 매칭
            if command == '일반몹':
                monster_type = '일반몹'
            elif command == '특수몹':
                monster_type = '특수몹'
            elif command == '보스몹':
                monster_type = '보스몹'
            # 단축키 매칭
            elif command in ['normal', 'n', '1']:
                monster_type = '일반몹'
            elif command in ['special', 's', '2']:
                monster_type = '특수몹'
            elif command in ['boss', 'b', '3']:
                monster_type = '보스몹'
        
        # command가 없거나 매칭되지 않으면 monster_names에서 확인 (가장 정확)
        if monster_type == "일반몹" and hasattr(game, 'monster_names') and game.monster_names:
            # monster_names의 키를 확인하여 타입 결정
            available_types = list(game.monster_names.keys())
            if available_types:
                # command와 일치하는 타입이 있으면 사용
                if command and command in available_types:
                    monster_type = command
                # 아니면 가장 최근에 추가된 타입 사용 (마지막 키)
                else:
                    monster_type = available_types[-1]
        
        # 그래도 못 찾으면 response에서 확인 (마지막 수단)
        if monster_type == "일반몹":
            # response에서 명시적으로 언급된 타입 확인
            # 단, 통계 메시지("일반몹: X마리")는 무시
            if '특수몹' in response:
                # "특수몹"이 "일반몹"보다 먼저 나오는지 확인
                special_idx = response.find('특수몹')
                normal_idx = response.find('일반몹')
                if special_idx != -1 and (normal_idx == -1 or special_idx < normal_idx):
                    monster_type = '특수몹'
            elif '보스몹' in response:
                boss_idx = response.find('보스몹')
                normal_idx = response.find('일반몹')
                if boss_idx != -1 and (normal_idx == -1 or boss_idx < normal_idx):
                    monster_type = '보스몹'
        
        # 몬스터 이름 추출
        if hasattr(game, 'monster_names') and monster_type in game.monster_names:
            monster_name = game.monster_names[monster_type]
        elif hasattr(game, 'monster_names') and game.monster_names:
            # monster_names에 있지만 타입이 다른 경우, 첫 번째 사용
            monster_name = list(game.monster_names.values())[0]
        
        return {
            'monster_name': monster_name,
            'monster_type': monster_type,
            'reward': reward,
            'is_success': is_success,
            'level': level,
            'gold': gold
        }

