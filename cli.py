#!/usr/bin/env python3
"""
CLI 테스트 모드 - 로컬에서 게임 봇을 테스트할 수 있는 인터페이스
"""
import readline
from game_engine import GameEngine
from config import Config

# readline 설정 (한글 입력 개선)
try:
    # macOS/Linux에서 한글 입력 개선
    readline.parse_and_bind("set editing-mode emacs")
    readline.parse_and_bind("set convert-meta off")
    readline.parse_and_bind("set input-meta on")
    readline.parse_and_bind("set output-meta on")
except (ImportError, AttributeError):
    pass  # readline이 없는 환경에서는 무시


class CLIMode:
    """CLI 모드 클래스"""

    def __init__(self):
        self.engine = GameEngine()
        self.current_user = "test_user"
        self.running = True

    def print_banner(self):
        """시작 배너 출력"""
        banner = """
╔═══════════════════════════════════════╗
║        GameBot - CLI 테스트 모드      ║
╚═══════════════════════════════════════╝
"""
        print(banner)
        print(f"👤 현재 사용자: {self.current_user}")

        # 신규 사용자 초기 골드 지급
        is_new_user = (
            self.engine.point_system.ensure_initial_points(self.current_user)
        )
        points = self.engine.point_system.get_points(self.current_user)

        if is_new_user:
            print(
                f"🎉 환영합니다! 신규 사용자에게 "
                f"{Config.INITIAL_POINTS}G를 지급했습니다!"
            )

        print(f"💰 골드: {points}G")
        print("\n💡 '도움말' 또는 'h'를 입력하면 명령어를 확인할 수 있습니다.")
        print("💡 '종료' 또는 'q'를 입력하면 프로그램을 종료합니다.")
        print(
            "💡 모든 명령어에 단축키가 있습니다! "
            "(예: g=골드, gl=게임목록, s=게임시작)"
        )
        print(
            "💡 슬래시 커맨드도 사용 가능합니다! "
            "(예: /골드, /게임시작 모험)\n"
        )
        print("=" * 50)

    def print_help(self):
        """도움말 출력"""
        help_text = """
📋 사용 가능한 명령어 (단축키):

🎮 게임 관련:
  - 게임목록 (g, gl)          : 사용 가능한 게임 목록 보기
  - 게임시작 [게임] (s, gs)   : 게임 시작
    예: s n, s 1, s number → 숫자맞추기
        s r, s 2, s rps → 가위바위보
        s a, s 3, s adventure → 모험
    슬래시 커맨드: /게임시작 모험, /s a
  - 게임종료 (e, end, ge)     : 현재 게임 종료

💰 골드 관련:
  - 골드 (g, gold, p, pt)            : 내 골드 조회
  - /골드, @게임봇 골드              : 슬래시/@ 커맨드로도 사용 가능
  - 골드주기 [사용자] [금액] (pay, send):
    다른 사용자에게 골드 전송
    예: pay alice 50, send bob 100, /골드주기 alice 50
  - 리더보드 (l, lb, rank)    : 골드 랭킹 보기

👤 사용자 관련:
  - 사용자 [이름] (u, user)   : 사용자 변경

❓ 기타:
  - 도움말 (h, ?)             : 이 도움말 보기
  - 종료 (q, quit)            : 프로그램 종료

게임 중에는 게임 명령을 입력하세요.
"""
        print(help_text)

    def process_command(self, command: str) -> str:
        """명령 처리"""
        command = command.strip()

        if not command:
            return ""

        # 사용자 변경 (단축키: u, user)
        msg_lower = command.lower()
        if (command.startswith('사용자 ') or
                msg_lower.startswith('u ') or
                msg_lower.startswith('user ')):
            if msg_lower.startswith('u '):
                new_user = command[2:].strip()
            elif msg_lower.startswith('user '):
                new_user = command[5:].strip()
            else:
                new_user = command.replace('사용자 ', '').strip()
            if new_user:
                self.current_user = new_user
                # 신규 사용자 초기 골드 지급
                is_new_user = (
                    self.engine.point_system.ensure_initial_points(
                        self.current_user
                    )
                )
                points = self.engine.point_system.get_points(self.current_user)

                response = (
                    f"✅ 사용자가 '{self.current_user}'로 "
                    f"변경되었습니다.\n💰 골드: {points}G"
                )
                if is_new_user:
                    response = (
                        f"✅ 사용자가 '{self.current_user}'로 "
                        f"변경되었습니다.\n🎉 신규 사용자에게 "
                        f"{Config.INITIAL_POINTS}G를 지급했습니다!\n"
                        f"💰 골드: {points}G"
                    )
                return response
            return "❌ 사용자 이름을 입력해주세요."

        # 엔진에 명령 전달
        return self.engine.process_message(self.current_user, command)

    def run(self):
        """CLI 모드 실행"""
        self.print_banner()

        try:
            while self.running:
                try:
                    # 입력 받기 (한글 입력 개선)
                    try:
                        user_input = input(
                            f"\n[{self.current_user}] > "
                        ).strip()
                    except UnicodeDecodeError:
                        # 인코딩 문제 시 재시도
                        print(
                            "\n⚠️ 입력 인코딩 오류가 발생했습니다. "
                            "다시 입력해주세요."
                        )
                        continue

                    if not user_input:
                        continue

                    # 종료 명령
                    if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                        print("\n👋 프로그램을 종료합니다.")
                        break

                    # 도움말
                    if user_input.lower() in ['help', '도움말', '?', 'h']:
                        self.print_help()
                        continue

                    # 명령 처리
                    response = self.process_command(user_input)

                    if response:
                        print(f"\n🤖 봇: {response}")

                except KeyboardInterrupt:
                    print("\n\n👋 프로그램을 종료합니다.")
                    break
                except EOFError:
                    print("\n\n👋 프로그램을 종료합니다.")
                    break
                except (ValueError, KeyError, AttributeError) as e:
                    print(f"\n❌ 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()

        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다.")


def main():
    """메인 함수"""
    cli = CLIMode()
    cli.run()


if __name__ == '__main__':
    main()
