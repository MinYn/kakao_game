#!/usr/bin/env python3
"""
게임 봇 메인 실행 파일
"""
import sys
from typing import Optional
from game_engine import GameEngine
from platforms.kakao_adapter import KakaoAdapter
from platforms.discord_adapter import DiscordAdapter
from config import Config


class GameBot:
    """게임 봇 메인 클래스"""
    
    def __init__(self, platform_type: Optional[str] = None):
        self.engine = GameEngine()
        platform = platform_type or Config.PLATFORM
        self.platform = self._create_platform(platform)
        self.platform.set_message_handler(self._handle_message)
        self.webhook_server = None
    
    def _create_platform(self, platform_type: str):
        """플랫폼 생성"""
        platform_type = platform_type.lower()
        
        if platform_type == 'kakao':
            return KakaoAdapter()
        elif platform_type == 'discord':
            return DiscordAdapter()
        else:
            raise ValueError(f"지원하지 않는 플랫폼: {platform_type}")
    
    def _handle_message(self, user_id: str, message: str) -> str:
        """메시지 핸들러"""
        try:
            return self.engine.process_message(user_id, message)
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"
    
    def start(self, start_webhook: bool = True, use_webhook: bool = True):
        """봇 시작
        
        Args:
            start_webhook: 웹훅 서버 시작 여부 (deprecated)
            use_webhook: 웹훅 서버 사용 여부 (기본값: True, 웹훅 서버만 사용)
        """
        print("게임 봇을 시작합니다...")
        
        # 카카오톡은 항상 웹훅 서버 모드 사용
        if isinstance(self.platform, KakaoAdapter):
            try:
                from webhook_server import create_webhook_server
                self.webhook_server = create_webhook_server(self.platform, self.engine)
                
                # 웹훅 서버는 별도 스레드에서 실행
                import threading
                server_thread = threading.Thread(
                    target=self.webhook_server.run,
                    daemon=True
                )
                server_thread.start()
                print(f"✅ 웹훅 서버 모드로 시작되었습니다 (완전 무료)")
                print(f"웹훅 URL: http://{Config.SERVER_HOST}:{Config.SERVER_PORT}/webhook")
                print("💡 카카오 챗봇 관리자센터에서 위 URL을 스킬 서버로 등록하세요")
                print("💡 자세한 설정: CHATBOT_ADMIN_GUIDE.md 참조")
                return
            except ImportError:
                print("⚠️ FastAPI가 설치되지 않았습니다. 웹훅 서버를 사용할 수 없습니다.")
                print("💡 설치: pip install fastapi uvicorn")
                return
        
        # 다른 플랫폼 (Discord 등)
        self.platform.start(start_webhook=False)
    
    def stop(self):
        """봇 종료"""
        print("게임 봇을 종료합니다...")
        self.platform.stop()


def main():
    """메인 함수"""
    # CLI 모드 체크
    if len(sys.argv) > 1 and sys.argv[1] in ['cli', 'test', '--cli', '--test']:
        from cli import CLIMode
        cli = CLIMode()
        cli.run()
        return
    
    # 설정 유효성 검사
    if not Config.validate():
        print("⚠️ 설정 파일(.env)을 확인해주세요.")
        print("💡 .env.example 파일을 참고하여 .env 파일을 생성하세요.")
    
    # 플랫폼 선택 (명령줄 인자 또는 설정 파일)
    platform = sys.argv[1] if len(sys.argv) > 1 else None
    
    bot = GameBot(platform_type=platform)
    
    try:
        # 플랫폼별 처리
        if platform == 'kakao':
            bot.start(use_webhook=True)
            print("\n✅ 카카오톡 웹훅 서버 모드로 실행 중... (완전 무료)")
            print("웹훅 서버가 실행되었습니다.")
            print("카카오 챗봇 관리자센터에서 스킬 서버 URL을 등록하세요.")
            print("💡 자세한 설정: CHATBOT_ADMIN_GUIDE.md 참조")
            print("\n종료하려면 Ctrl+C를 누르세요.")
            
            # 서버가 계속 실행되도록 대기
            import time
            while True:
                time.sleep(1)
        elif platform == 'discord':
            print("\n✅ 디스코드 모드로 실행 중...")
            print("디스코드 봇이 실행되었습니다.")
            print("\n종료하려면 Ctrl+C를 누르세요.")
            import time
            while True:
                time.sleep(1)
        else:
            print("\n💡 CLI 모드로 테스트하려면: python main.py cli")
            print("💡 또는: python cli.py")
        
    except KeyboardInterrupt:
        print("\n종료 중...")
    finally:
        bot.stop()


if __name__ == '__main__':
    main()

