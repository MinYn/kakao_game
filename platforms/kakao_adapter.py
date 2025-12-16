from typing import Optional
from platforms.base_platform import ChatPlatform


class KakaoAdapter(ChatPlatform):
    """카카오톡 채팅봇 어댑터 (웹훅 서버 사용)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.is_running = False
    
    def send_message(self, user_id: str, message: str) -> bool:
        """카카오톡 메시지 전송 (웹훅 서버에서 처리)"""
        # 웹훅 서버 모드에서는 실제 메시지 전송은 웹훅 서버가 처리
        # 이 메서드는 호환성을 위해 유지 (시뮬레이션 출력)
        print(f"[카카오톡 → {user_id}] {message}")
        return True
    
    def start(self, start_webhook: bool = True) -> None:
        """카카오톡 봇 시작 (웹훅 서버 모드)"""
        if self.is_running:
            print("[카카오톡] 이미 실행 중입니다.")
            return
        
        self.is_running = True
        print("[카카오톡] 웹훅 서버 모드로 시작합니다.")
    
    def stop(self) -> None:
        """카카오톡 봇 종료"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("[카카오톡] 봇이 종료되었습니다.")
    
    def simulate_message(self, user_id: str, message: str) -> None:
        """테스트용 메시지 시뮬레이션"""
        if self.message_handler:
            response = self.message_handler(user_id, message)
            if response:
                self.send_message(user_id, response)

