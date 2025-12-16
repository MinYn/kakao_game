from abc import ABC, abstractmethod
from typing import Callable, Optional


class ChatPlatform(ABC):
    """채팅 플랫폼 기본 인터페이스"""
    
    def __init__(self):
        self.message_handler: Optional[Callable[[str, str], str]] = None
    
    @abstractmethod
    def send_message(self, user_id: str, message: str) -> bool:
        """메시지 전송"""
        pass
    
    @abstractmethod
    def start(self) -> None:
        """플랫폼 시작"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """플랫폼 종료"""
        pass
    
    def set_message_handler(self, handler: Callable[[str, str], str]) -> None:
        """메시지 핸들러 설정"""
        self.message_handler = handler
    
    def handle_message(self, user_id: str, message: str) -> Optional[str]:
        """메시지 처리"""
        if self.message_handler:
            return self.message_handler(user_id, message)
        return None

