#!/usr/bin/env python3
"""
CLI 테스트 모드 - 로컬에서 게임 봇을 테스트할 수 있는 인터페이스
"""
from game_engine import GameEngine
from platforms.cli_adapter import CLIAdapter


def main():
    """메인 함수"""
    engine = GameEngine()
    platform = CLIAdapter(engine=engine)
    platform.set_message_handler(
        lambda user_id, message: engine.process_message(
            user_id,
            message,
            platform_adapter=platform,
        )
    )
    platform.start()


if __name__ == '__main__':
    main()
