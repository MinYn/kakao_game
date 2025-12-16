from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Game(ABC):
    """게임 기본 클래스"""
    
    def __init__(self, user_id: str, point_system=None):
        self.user_id = user_id
        self.is_active = False
        self.game_data: Dict[str, Any] = {}
        self.point_system = point_system  # 골드 시스템 참조
    
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
    
    def award_points(self, amount: int, reason: str = "") -> int:
        """골드 지급"""
        if self.point_system:
            return self.point_system.add_points(self.user_id, amount, reason)
        return 0
    
    def deduct_points(self, amount: int, reason: str = "") -> Optional[int]:
        """골드 차감"""
        if self.point_system:
            return self.point_system.deduct_points(self.user_id, amount, reason)
        return None
    
    def get_user_points(self) -> int:
        """사용자 골드 조회"""
        if self.point_system:
            return self.point_system.get_points(self.user_id)
        return 0

