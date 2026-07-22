from typing import Dict, Optional, List, Tuple, Any
from platforms.base_platform import ChatPlatform
from games.base_game import Game
from games.adventure import AdventureGame
from gold_system_postgres import GoldSystemPostgres
from config import Config


class GameEngine:
    """게임 엔진 - 게임 관리 및 명령 처리"""
    
    def __init__(self, gold_system: Optional[GoldSystemPostgres] = None):
        self.active_games: Dict[str, Game] = {}
        self.gold_system = gold_system or GoldSystemPostgres()
        self._platform_adapter: Optional[ChatPlatform] = None
        self.command_definitions = self._build_command_definitions()
        self._command_index: Dict[str, Dict[str, Any]] = {}
        self.default_game_class = AdventureGame
    
    def process_message(self, user_id: str, message: str, user_name: Optional[str] = None, platform_adapter=None) -> str:
        """사용자 메시지 처리
        
        Args:
            user_id: 사용자 ID
            message: 메시지 내용
            user_name: 사용자 이름 (선택사항, 멘션용)
            platform_adapter: 플랫폼 어댑터 (멘션 기능용, 선택사항)
        """
        # 신규 사용자 초기 골드 지급
        is_new_user = self.gold_system.ensure_initial_gold(user_id)
        
        # 플랫폼 어댑터 저장 (멘션 기능용)
        if platform_adapter:
            self._platform_adapter = platform_adapter
        elif not hasattr(self, '_platform_adapter'):
            self._platform_adapter = None
        
        message = self._normalize_command(message)

        # 구조화된 기본 명령어 처리
        handled, command_key = self._run_engine_command(
            user_id,
            message,
            user_name=user_name,
            is_new_user=is_new_user,
        )
        if handled:
            return handled
        
        start_response = self._ensure_active_game(user_id)

        # 활성 게임이 있으면 게임 명령 처리
        if user_id in self.active_games:
            game = self.active_games[user_id]
            if game.is_game_active():
                game_response = game.process_command(message)
                if start_response and game_response:
                    return f"{start_response}\n\n{game_response}"
                return game_response or start_response or ""

        # 기본 응답
        return self._get_help()

    def _normalize_command(self, message: str) -> str:
        message = message.strip()
        if message.startswith('/'):
            return message[1:].strip()
        if message.startswith('@'):
            parts = message[1:].split(None, 1)
            if len(parts) > 1:
                return parts[1].strip()
            return ''
        return message

    def _ensure_active_game(self, user_id: str) -> Optional[str]:
        """사용자에게 기본 게임 인스턴스를 보장"""
        existing = self.active_games.get(user_id)
        if existing and existing.is_game_active():
            return None

        try:
            game = self.default_game_class(user_id, point_system=self.gold_system)
            self.active_games[user_id] = game
            return game.start()
        except Exception as e:
            return f"게임을 준비하는 중 오류가 발생했습니다: {str(e)}"

    def _build_command_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": "gold",
                "label": "💰 골드",
                "triggers": [
                    '골드', 'gold', 'g', '포인트', 'point', 'points',
                    '잔액', '내골드', 'p', 'pt'
                ],
                "handler": self._handle_gold_command,
                "match": "exact",
                "button": {"label": "💰 골드", "messageText": "골드"},
            },
            {
                "key": "leaderboard",
                "label": "🏆 리더보드",
                "triggers": ['리더보드', '랭킹', 'leaderboard', 'ranking', 'l', 'lb', 'rank', 'r'],
                "handler": self._get_leaderboard,
                "match": "exact",
                "button": {"label": "🏆 랭킹", "messageText": "리더보드"},
            },
            {
                "key": "help",
                "label": "❓ 도움말",
                "triggers": ['도움말', 'help', '?', 'h'],
                "handler": self._get_help,
                "match": "exact",
                "button": {"label": "❓ 도움말", "messageText": "도움말"},
            },
            {
                "key": "transfer",
                "label": "💸 골드주기",
                "triggers": ['골드주기', '골드전송', 'pay ', 'send '],
                "handler": self._handle_transfer_command,
                "match": "prefix",
            },
        ]

    def _build_command_index(self) -> None:
        self._command_index = {}
        for definition in self.command_definitions:
            for trigger in definition.get("triggers", []):
                self._command_index[trigger.lower()] = definition

    def _resolve_command_definition(self, command: str) -> Optional[Dict[str, Any]]:
        if not self._command_index:
            self._build_command_index()

        key = command.strip().lower()
        for trigger, definition in self._command_index.items():
            match_type = definition.get("match", "exact")
            if match_type == "prefix":
                if key.startswith(trigger):
                    return definition
            elif key == trigger:
                return definition
        return None

    def _run_engine_command(
        self,
        user_id: str,
        command: str,
        user_name: Optional[str] = None,
        is_new_user: bool = False,
    ) -> tuple[Optional[str], Optional[str]]:
        definition = self._resolve_command_definition(command)
        if not definition:
            return None, None

        handler = definition.get("handler")
        if not handler:
            return None, None

        if handler in (self._get_leaderboard, self._get_help):
            result = handler()
        elif handler is self._handle_transfer_command:
            result = handler(user_id, command)
        else:
            result = handler(user_id, user_name=user_name, is_new_user=is_new_user)

        return result, definition.get("key")

    def _handle_gold_command(self, user_id: str, user_name: Optional[str] = None, is_new_user: bool = False) -> str:
        response = self._get_gold(user_id)
        if is_new_user:
            response = (
                f"🎉 환영합니다! 신규 사용자에게 "
                f"{Config.INITIAL_GOLD}G를 지급했습니다!\n\n"
                f"{response}"
            )
        mention = self._get_user_mention(user_id, user_name)
        if mention:
            response = f"{mention} {response}"
        return response

    def _handle_transfer_command(self, user_id: str, message: str) -> str:
        msg_lower = message.lower()
        if msg_lower.startswith('pay '):
            message = '골드주기 ' + message[4:]
        elif msg_lower.startswith('send '):
            message = '골드주기 ' + message[5:]
        return self._transfer_gold(user_id, message)
    
    def _get_help(self) -> str:
        """도움말 반환"""
        help_text = [
            "🎮 게임 봇 도움말",
            "",
            "기본 명령어:",
            "- 골드 (g, gold, p, pt): 내 골드 조회",
            "- 골드주기 [사용자] [금액] (pay, send): 다른 사용자에게 골드 전송",
            "- 리더보드 (l, lb, rank): 골드 랭킹 보기",
            "- 도움말 (h, ?): 이 도움말 보기",
            "",
            "모험 명령어:",
            "- 성장/강화: '성장', '강화', '업그레이드'",
            "- 정산/판매: '정산', '판매'",
            "- 출동: '출동', 'mission' (정찰·탐사·구조 랜덤 이벤트)",
            "- 상태/패스 확인: '상태', '패스'",
            "",
            "첫 메시지를 보내면 바로 우주 탐험이 시작되며 버튼으로 바로 진행할 수 있습니다."
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
    
    def _end_game(self, user_id: Optional[str] = None, *_: Any, **__: Any) -> str:
        """게임 종료"""
        if not user_id:
            return "사용자 정보를 확인할 수 없어 게임을 종료할 수 없습니다."

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
        
        # 받는 사람 멘션
        to_user_mention = self._get_user_mention(to_user)
        
        response = f"""✅ 골드 전송 완료!

보낸 사람: {from_user}
받은 사람: {to_user_mention if to_user_mention else to_user}
전송 금액: {amount}G

{from_user}의 남은 골드: {self.gold_system.get_gold(from_user)}G
{to_user_mention if to_user_mention else to_user}의 현재 골드: {result}G"""
        
        return response
    
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
    
    def get_ui_buttons(self, user_id: str, command: str | None = None, response: str | None = None) -> List[Dict[str, str]]:
        """UI 버튼 목록 반환 (플랫폼별 UI 생성용)

        Args:
            user_id: 사용자 ID
            command: 직전에 실행한 명령어 (UI 맥락 판단용)
            response: 응답 메시지 (선택사항, 후행 UI 판단용)

        Returns:
            버튼 목록 [{'label': '...', 'messageText': '...'}, ...]
        """
        active_game = self.active_games.get(user_id)
        game_buttons: List[Dict[str, str]] = []

        if active_game and active_game.is_game_active():
            if hasattr(active_game, "get_command_buttons"):
                game_buttons = active_game.get_command_buttons(command) or []

        base_buttons = self._build_base_buttons()

        combined = game_buttons + base_buttons
        # 최대 5개로 제한
        return combined[:5]

    def _build_base_buttons(self) -> List[Dict[str, str]]:
        buttons: List[Dict[str, str]] = []
        for definition in self.command_definitions:
            button_meta = definition.get("button")
            if not button_meta:
                continue
            buttons.append({
                "label": button_meta.get("label", definition.get("label", "")),
                "messageText": button_meta.get("messageText", ""),
            })
        return buttons
    
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
        
        # 성장 결과 확인
        if '성장 성공' in response or '성장 실패' in response:
            return user_id in self.active_games

        # 활동 결과 확인
        if '활동 성공' in response or '활동이 잘 풀리지' in response:
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
    
    def _get_user_mention(self, user_id: str, user_name: Optional[str] = None) -> Optional[str]:
        """사용자 멘션 문자열 생성
        
        Args:
            user_id: 사용자 ID
            user_name: 사용자 이름 (선택사항)
            
        Returns:
            멘션 문자열 또는 None (플랫폼 어댑터가 없으면 None)
        """
        if self._platform_adapter and hasattr(self._platform_adapter, 'mention_user'):
            return self._platform_adapter.mention_user(user_id, user_name)
        return None
    
    def set_platform_adapter(self, adapter):
        """플랫폼 어댑터 설정 (멘션 기능용)"""
        self._platform_adapter = adapter

    def get_badge_offset(self, user_id: str) -> int:
        """배지 변경 오프셋 조회"""
        game = self.active_games.get(user_id)
        if not game or not hasattr(game, "game_data"):
            return 0
        return int(game.game_data.get("badge_cycle", 0))

    def get_badge_upgrade_stage(self, user_id: str) -> int:
        """본체 +N 기반 배지 업그레이드 단계 (attempts 기반 폐기)."""
        game = self.active_games.get(user_id)
        if game and hasattr(game, "get_badge_upgrade_stage"):
            return int(game.get_badge_upgrade_stage())
        if game and hasattr(game, "ship_progress"):
            from games.ship_system import body_enhance_to_upgrade_stage

            return body_enhance_to_upgrade_stage(game.ship_progress.body_enhance)
        if game and hasattr(game, "current_level"):
            from games.ship_system import body_enhance_to_upgrade_stage

            return body_enhance_to_upgrade_stage(int(game.current_level))
        return 0

    def get_badge_ship_grade(self, user_id: str) -> str:
        """활성 기체 등급(F~S) — 배지 마크용."""
        game = self.active_games.get(user_id)
        if game and hasattr(game, "get_ship_grade_value"):
            return game.get_ship_grade_value()
        if game and hasattr(game, "ship_progress"):
            return game.ship_progress.grade.value
        return "F"

    def get_badge_body_enhance(self, user_id: str) -> int:
        """활성 기체 본체 +N — 배지 하단 숫자 스타일용."""
        game = self.active_games.get(user_id)
        if game and hasattr(game, "ship_progress"):
            return int(game.ship_progress.body_enhance)
        if game and hasattr(game, "current_level"):
            return int(game.current_level)
        return 0
    
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
