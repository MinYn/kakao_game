from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class Game(ABC):
    """게임 기본 클래스"""
    
    def __init__(self, user_id: str, point_system=None):
        self.user_id = user_id
        self.is_active = False
        self.game_data: Dict[str, Any] = {}
        self.point_system = point_system  # 골드 시스템 참조
        self._command_index: Dict[str, Dict[str, Any]] = {}
    
    @abstractmethod
    def start(self) -> str:
        """게임 시작 메시지 반환"""
        pass
    
    @abstractmethod
    def process_command(self, command: str) -> str:
        """사용자 명령 처리"""
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        """도움말 반환"""
        pass
    
    def end(self) -> str:
        """게임 종료"""
        self.is_active = False
        self.game_data.clear()
        return "게임이 종료되었습니다."
    
    def is_game_active(self) -> bool:
        """게임 활성 상태 확인"""
        return self.is_active
    
    def award_gold(self, amount: int, reason: str = "") -> int:
        """골드 지급"""
        if self.point_system:
            return self.point_system.add_gold(self.user_id, amount, reason)
        return 0
    
    def deduct_gold(self, amount: int, reason: str = "") -> Optional[int]:
        """골드 차감"""
        if self.point_system:
            return self.point_system.deduct_gold(self.user_id, amount, reason)
        return None
    
    def get_user_points(self) -> int:
        """사용자 골드 조회"""
        if self.point_system:
            return self.point_system.get_gold(self.user_id)
        return 0

    # ===== 구조화된 커맨드 헬퍼 =====
    def get_command_definitions(self) -> List[Dict[str, Any]]:
        """서브클래스에서 정의한 커맨드 메타데이터 반환"""
        return getattr(self, "command_definitions", [])

    def _build_command_index(self) -> None:
        """트리거 → 커맨드 정의 매핑 준비"""
        self._command_index = {}
        for definition in self.get_command_definitions():
            for trigger in definition.get("triggers", []):
                self._command_index[trigger.lower()] = definition

    def _resolve_command_definition(self, command: str) -> Optional[Dict[str, Any]]:
        if not self._command_index:
            self._build_command_index()

        key = command.strip().lower()
        return self._command_index.get(key)

    def run_structured_command(self, command: str) -> tuple[Optional[str], Optional[str]]:
        """구조화된 커맨드 정의 기반으로 명령 실행"""
        definition = self._resolve_command_definition(command)
        if not definition:
            return None, None

        handler = definition.get("handler")
        if not handler:
            return None, None

        result = handler()
        return result, definition.get("key")

    def get_command_buttons(self, last_command: Optional[str] = None) -> List[Dict[str, str]]:
        """구조화된 커맨드 정의를 활용해 버튼 데이터 반환"""
        buttons: List[Dict[str, str]] = []
        for definition in self.get_command_definitions():
            button_meta = definition.get("button")
            if not button_meta:
                continue

            label = button_meta.get("label") or definition.get("label")
            message_text = button_meta.get("messageText") or next(
                iter(definition.get("triggers", [])),
                "",
            )

            if label and message_text:
                buttons.append({"label": label, "messageText": message_text})

        return buttons

