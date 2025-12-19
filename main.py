#!/usr/bin/env python3
"""
게임 봇 메인 실행 파일
"""
import sys
from typing import Optional
from game_engine import GameEngine
from platforms.discord_adapter import DiscordAdapter
from platforms.cli_adapter import CLIAdapter
from config import Config
from events.platform_queue import PlatformMessage, PlatformMessageQueue


class GameBot:
    """게임 봇 메인 클래스"""
    
    def __init__(self, platform_type: Optional[str] = None):
        self.engine = GameEngine()
        self.message_queue = PlatformMessageQueue()
        platform = platform_type or Config.PLATFORM
        self.platform = self._create_platform(platform)
        self.platform.set_message_handler(self._handle_message)
        if hasattr(self.platform, "set_message_queue"):
            self.platform.set_message_queue(self.message_queue)
    
    def _create_platform(self, platform_type: str):
        """플랫폼 생성"""
        platform_type = platform_type.lower()

        if platform_type == 'discord':
            return DiscordAdapter(engine=self.engine, message_queue=self.message_queue)
        elif platform_type == 'cli':
            return CLIAdapter(engine=self.engine)
        raise ValueError(f"지원하지 않는 플랫폼: {platform_type}")
    
    def _handle_message(self, user_id: str, message: str) -> str:
        """메시지 핸들러"""
        try:
            # 플랫폼 어댑터 설정 (멘션 기능용)
            self.engine.set_platform_adapter(self.platform)
            return self.engine.process_message(user_id, message, platform_adapter=self.platform)
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"

    def _start_message_pipeline(self) -> None:
        """Kafka/인메모리 큐를 통한 메시지 라우팅 시작"""

        def process_incoming(message: PlatformMessage) -> None:
            response = self._handle_message(message.user_id, message.content)
            if response:
                self.message_queue.publish_outgoing(
                    PlatformMessage(
                        platform=message.platform,
                        user_id=message.user_id,
                        content=response,
                        correlation_id=message.correlation_id,
                    )
                )

        self.message_queue.start_incoming_consumer(process_incoming, group_id=f"{Config.KAFKA_PLATFORM_GROUP}-engine")

    def start(self) -> None:
        """봇 시작"""
        print("게임 봇을 시작합니다...")
        self._start_message_pipeline()
        self.platform.start()

    def stop(self):
        """봇 종료"""
        print("게임 봇을 종료합니다...")
        try:
            # 플랫폼 종료
            if self.platform:
                self.platform.stop()

            # 게임 엔진 데이터 저장
            if self.engine:
                # 모든 활성 게임 종료 및 데이터 저장
                if hasattr(self.engine, 'active_games'):
                    for user_id in list(self.engine.active_games.keys()):
                        try:
                            game = self.engine.active_games.get(user_id)
                            if game and hasattr(game, 'end'):
                                game.end()
                        except Exception as e:
                            print(f"게임 종료 오류 (user_id: {user_id}): {e}")

                # 데이터베이스 연결 정리
                if hasattr(self.engine, 'point_system') and self.engine.gold_system:
                    # PostgreSQL 연결 풀은 자동으로 관리됨
                    pass
        except Exception as e:
            print(f"종료 중 오류: {e}")
        try:
            if self.message_queue:
                self.message_queue.stop()
        except Exception as e:
            print(f"메시지 큐 종료 오류: {e}")


def main():
    """메인 함수"""
    # 설정 유효성 검사
    if not Config.validate():
        print("⚠️ 설정 파일(.env)을 확인해주세요.")
        print("💡 .env.example 파일을 참고하여 .env 파일을 생성하세요.")
    
    # 플랫폼 선택 (명령줄 인자 또는 설정 파일)
    platform = sys.argv[1] if len(sys.argv) > 1 else Config.PLATFORM

    bot = GameBot(platform_type=platform)

    try:
        bot.start()
        if platform == 'discord':
            print("\n✅ 디스코드 모드로 실행 중...")
            import time

            while True:
                time.sleep(1)
        else:
            print("\n💡 CLI 모드로 테스트하려면: python main.py cli")
            print("💡 또는: python cli.py")

    except KeyboardInterrupt:
        print("\n종료 신호를 받았습니다...")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            bot.stop()
        except Exception as e:
            print(f"종료 중 오류: {e}")
        print("✅ 봇이 안전하게 종료되었습니다.")


if __name__ == '__main__':
    main()
