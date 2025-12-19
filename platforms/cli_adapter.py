#!/usr/bin/env python3
"""
CLI 테스트 모드 - 로컬에서 게임 봇을 테스트할 수 있는 인터페이스
"""
import readline
from typing import Optional, TYPE_CHECKING

from platforms.base_platform import ChatPlatform
from config import Config

if TYPE_CHECKING:
    from game_engine import GameEngine

# readline 설정 (한글 입력 개선)
try:
    # macOS/Linux에서 한글 입력 개선
    readline.parse_and_bind("set editing-mode emacs")
    readline.parse_and_bind("set convert-meta off")
    readline.parse_and_bind("set input-meta on")
    readline.parse_and_bind("set output-meta on")
except (ImportError, AttributeError):
    pass  # readline이 없는 환경에서는 무시


class CLIAdapter(ChatPlatform):
    """CLI 모드 어댑터"""

    def __init__(self, engine: Optional["GameEngine"] = None):
        super().__init__()
        self.engine = engine
        self.current_user = "test_user"
        self.running = True

    def send_message(self, user_id: str, message: str) -> bool:
        """메시지 전송 (CLI 출력)"""
        print(f"\n🤖 봇: {message}")
        return True

    def start(self) -> None:
        """CLI 시작"""
        self._print_banner()
        self._run_loop()

    def stop(self) -> None:
        """CLI 종료"""
        self.running = False

    def mention_user(self, user_id: str, user_name: Optional[str] = None) -> str:
        """사용자 멘션 문자열 생성"""
        return user_name or user_id

    def _print_banner(self) -> None:
        """시작 배너 출력"""
        banner = """
╔═══════════════════════════════════════╗
║        GameBot - CLI 테스트 모드      ║
╚═══════════════════════════════════════╝
"""
        print(banner)
        print(f"👤 현재 사용자: {self.current_user}")

        if self.engine:
            is_new_user = self.engine.gold_system.ensure_initial_gold(self.current_user)
            gold = self.engine.gold_system.get_gold(self.current_user)

            if is_new_user:
                print(
                    f"🎉 환영합니다! 신규 사용자에게 "
                    f"{Config.INITIAL_GOLD}G를 지급했습니다!"
                )

            print(f"💰 골드: {gold}G")

        print("\n💡 '도움말'을 입력하면 사용법을 확인할 수 있습니다.")
        print("💡 '종료' 또는 'q'를 입력하면 프로그램을 종료합니다.")
        print("=" * 50)

    def _run_loop(self) -> None:
        """CLI 입력 루프"""
        try:
            while self.running:
                try:
                    try:
                        user_input = input(
                            f"\n[{self.current_user}] > "
                        ).strip()
                    except UnicodeDecodeError:
                        print(
                            "\n⚠️ 입력 인코딩 오류가 발생했습니다. "
                            "다시 입력해주세요."
                        )
                        continue

                    if not user_input:
                        continue

                    if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                        print("\n👋 프로그램을 종료합니다.")
                        break

                    response = self._process_cli_input(user_input)
                    if response:
                        self.send_message(self.current_user, response)
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

    def _process_cli_input(self, command: str) -> str:
        """CLI 입력 처리"""
        command = command.strip()

        if not command:
            return ""

        if command.startswith('/user '):
            return self._switch_user(command.replace('/user ', '', 1).strip())
        if command.startswith('사용자 '):
            return self._switch_user(command.replace('사용자 ', '', 1).strip())

        if self.message_handler:
            return self.message_handler(self.current_user, command) or ""
        return "❌ 메시지 핸들러가 설정되지 않았습니다."

    def _switch_user(self, new_user: str) -> str:
        if not new_user:
            return "❌ 사용자 이름을 입력해주세요."

        self.current_user = new_user

        if not self.engine:
            return f"✅ 사용자가 '{self.current_user}'로 변경되었습니다."

        is_new_user = self.engine.gold_system.ensure_initial_gold(self.current_user)
        gold = self.engine.gold_system.get_gold(self.current_user)

        response = (
            f"✅ 사용자가 '{self.current_user}'로 변경되었습니다.\n"
            f"💰 골드: {gold}G"
        )
        if is_new_user:
            response = (
                f"✅ 사용자가 '{self.current_user}'로 변경되었습니다.\n"
                f"🎉 신규 사용자에게 {Config.INITIAL_GOLD}G를 지급했습니다!\n"
                f"💰 골드: {gold}G"
            )
        return response
