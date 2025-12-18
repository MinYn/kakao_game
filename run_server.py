#!/usr/bin/env python3
"""
디스코드 봇 실행용 스크립트 (단일 프로세스)
"""
from main import GameBot


def run_discord() -> None:
    """단일 프로세스로 디스코드 봇 실행"""
    bot = GameBot(platform_type='discord')
    try:
        bot.start()
        print("\n✅ 디스코드 모드로 실행 중...")
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n종료 신호를 받았습니다...")
    finally:
        bot.stop()


if __name__ == '__main__':
    run_discord()
