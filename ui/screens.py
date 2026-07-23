"""화면 ID · depth · 버튼 레지스트리.

이슈 #17 depth 트리와 동기화:
  D0 홈 MENU(5+4)
  D1 섹션 MENU(5+4) 또는 DETAIL(15+2)
  D2 결과 DETAIL(15+2)
  D3 서브 DETAIL(15+2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from ui.mobile_reply import LayoutMode


@dataclass(frozen=True)
class ButtonDef:
    label: str
    message_text: str

    def as_dict(self) -> dict:
        return {"label": self.label, "messageText": self.message_text}


@dataclass(frozen=True)
class ScreenDef:
    screen_id: str
    depth: int
    layout: LayoutMode
    buttons: tuple[ButtonDef, ...]
    description: str = ""

    def button_dicts(self) -> List[dict]:
        return [b.as_dict() for b in self.buttons]


def _btn(label: str, message: str) -> ButtonDef:
    return ButtonDef(label=label, message_text=message)


# ---- Screen catalog (issue #17) ----

D0_HOME = ScreenDef(
    screen_id="D0_HOME",
    depth=0,
    layout=LayoutMode.MENU,
    description="앱 진입·주요 4대 축",
    buttons=(
        _btn("🔨 성장", "성장"),
        _btn("🚀 출동", "출동"),
        _btn("📚 도감", "도감"),
        _btn("📊 상태", "상태"),
    ),
)

D1_GROW = ScreenDef(
    screen_id="D1_GROW",
    depth=1,
    layout=LayoutMode.MENU,
    description="성장 메뉴",
    buttons=(
        _btn("🔨 강화", "강화"),
        _btn("💰 판매", "판매"),
        _btn("📊 상태", "상세"),
        _btn("🏠 홈", "홈"),
    ),
)

D1_CODEX = ScreenDef(
    screen_id="D1_CODEX",
    depth=1,
    layout=LayoutMode.MENU,
    description="도감 요약",
    buttons=(
        _btn("📋 목록", "목록"),
        _btn("➡️ 다음", "다음"),
        _btn("🚀 내 기체", "상세"),
        _btn("🏠 홈", "홈"),
    ),
)

D1_STATUS = ScreenDef(
    screen_id="D1_STATUS",
    depth=1,
    layout=LayoutMode.MENU,
    description="상태 메뉴",
    buttons=(
        _btn("📋 상세", "상세"),
        _btn("💰 골드", "골드"),
        _btn("🎫 패스", "패스"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_ENHANCE_RESULT = ScreenDef(
    screen_id="D2_ENHANCE_RESULT",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="강화 결과",
    buttons=(
        _btn("🔨 다시 강화", "강화"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_SELL_RESULT = ScreenDef(
    screen_id="D2_SELL_RESULT",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="판매 결과",
    buttons=(
        _btn("🔨 성장", "성장"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_MISSION_RESULT = ScreenDef(
    screen_id="D2_MISSION_RESULT",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="출동 결과",
    buttons=(
        _btn("🚀 다시 출동", "출동"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_CODEX_PAGE = ScreenDef(
    screen_id="D2_CODEX_PAGE",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="도감 페이지",
    buttons=(
        _btn("➡️ 다음", "다음"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_GOLD = ScreenDef(
    screen_id="D2_GOLD",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="골드",
    buttons=(
        _btn("📊 상태", "상태"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_PASS = ScreenDef(
    screen_id="D2_PASS",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="패스",
    buttons=(
        _btn("🚀 출동", "출동"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_STATUS_DETAIL = ScreenDef(
    screen_id="D2_STATUS_DETAIL",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="상태 상세",
    buttons=(
        _btn("🔨 성장", "성장"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_HELP = ScreenDef(
    screen_id="D2_HELP",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="도움말",
    buttons=(
        _btn("🔨 성장", "성장"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_RANK = ScreenDef(
    screen_id="D2_RANK",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="리더보드",
    buttons=(
        _btn("💰 골드", "골드"),
        _btn("🏠 홈", "홈"),
    ),
)

D2_TRANSFER = ScreenDef(
    screen_id="D2_TRANSFER",
    depth=2,
    layout=LayoutMode.DETAIL,
    description="골드 전송",
    buttons=(
        _btn("💰 골드", "골드"),
        _btn("🏠 홈", "홈"),
    ),
)

D3_CODEX_PAGE = ScreenDef(
    screen_id="D3_CODEX_PAGE",
    depth=3,
    layout=LayoutMode.DETAIL,
    description="도감 추가 페이지",
    buttons=(
        _btn("➡️ 다음", "다음"),
        _btn("🏠 홈", "홈"),
    ),
)


_ALL_SCREENS: tuple[ScreenDef, ...] = (
    D0_HOME,
    D1_GROW,
    D1_CODEX,
    D1_STATUS,
    D2_ENHANCE_RESULT,
    D2_SELL_RESULT,
    D2_MISSION_RESULT,
    D2_CODEX_PAGE,
    D2_GOLD,
    D2_PASS,
    D2_STATUS_DETAIL,
    D2_HELP,
    D2_RANK,
    D2_TRANSFER,
    D3_CODEX_PAGE,
)


class ScreenRegistry:
    """screen_id → ScreenDef 조회 및 명령 → 화면 해석."""

    def __init__(self, screens: Sequence[ScreenDef] | None = None):
        self._by_id: Dict[str, ScreenDef] = {}
        for screen in screens or _ALL_SCREENS:
            self._by_id[screen.screen_id] = screen

    def get(self, screen_id: str) -> Optional[ScreenDef]:
        return self._by_id.get(screen_id)

    def require(self, screen_id: str) -> ScreenDef:
        screen = self.get(screen_id)
        if screen is None:
            raise KeyError(f"unknown screen_id: {screen_id}")
        return screen

    def buttons_for(self, screen_id: str) -> List[dict]:
        screen = self.get(screen_id) or D0_HOME
        return screen.button_dicts()

    def all_screens(self) -> List[ScreenDef]:
        return list(self._by_id.values())

    def validate_depth_graph(self) -> List[str]:
        """depth 0~3 및 DETAIL 홈 복귀 검증."""
        errors: List[str] = []
        for screen in self._by_id.values():
            if screen.depth < 0 or screen.depth > 3:
                errors.append(f"{screen.screen_id}: depth {screen.depth}")
            expected = screen.layout.button_count
            if len(screen.buttons) != expected:
                errors.append(
                    f"{screen.screen_id}: buttons {len(screen.buttons)} != {expected}"
                )
            if screen.layout is LayoutMode.DETAIL:
                messages = {b.message_text for b in screen.buttons}
                if "홈" not in messages:
                    errors.append(f"{screen.screen_id}: DETAIL missing 홈")
        return errors


_DEFAULT_REGISTRY = ScreenRegistry()


def get_screen(screen_id: str) -> Optional[ScreenDef]:
    return _DEFAULT_REGISTRY.get(screen_id)


def get_registry() -> ScreenRegistry:
    return _DEFAULT_REGISTRY


# 명령 키워드 → 기본 착지 화면 (텍스트 명령도 동일 레이아웃)
_COMMAND_SCREEN_MAP: Dict[str, str] = {
    # D0
    "홈": "D0_HOME",
    "home": "D0_HOME",
    "hub": "D0_HOME",
    "시작": "D0_HOME",
    # D1 menus
    "성장": "D1_GROW",
    "grow": "D1_GROW",
    "도감": "D1_CODEX",
    "collection": "D1_CODEX",
    "codex": "D1_CODEX",
    "수집": "D1_CODEX",
    "ships": "D1_CODEX",
    "상태": "D1_STATUS",
    "status": "D1_STATUS",
    "info": "D1_STATUS",
    # D2 actions
    "강화": "D2_ENHANCE_RESULT",
    "업그레이드": "D2_ENHANCE_RESULT",
    "개조": "D2_ENHANCE_RESULT",
    "train": "D2_ENHANCE_RESULT",
    "판매": "D2_SELL_RESULT",
    "정산": "D2_SELL_RESULT",
    "sell": "D2_SELL_RESULT",
    "추억": "D2_SELL_RESULT",
    "돌아보기": "D2_SELL_RESULT",
    "출동": "D2_MISSION_RESULT",
    "mission": "D2_MISSION_RESULT",
    "탐험": "D2_MISSION_RESULT",
    "go": "D2_MISSION_RESULT",
    "m": "D2_MISSION_RESULT",
    "0": "D2_MISSION_RESULT",
    "정찰": "D2_MISSION_RESULT",
    "walk": "D2_MISSION_RESULT",
    "scout": "D2_MISSION_RESULT",
    "n": "D2_MISSION_RESULT",
    "1": "D2_MISSION_RESULT",
    "탐사": "D2_MISSION_RESULT",
    "play": "D2_MISSION_RESULT",
    "survey": "D2_MISSION_RESULT",
    "s": "D2_MISSION_RESULT",
    "2": "D2_MISSION_RESULT",
    "특별놀이": "D2_MISSION_RESULT",
    "구조": "D2_MISSION_RESULT",
    "challenge": "D2_MISSION_RESULT",
    "rescue": "D2_MISSION_RESULT",
    "boss": "D2_MISSION_RESULT",
    "b": "D2_MISSION_RESULT",
    "3": "D2_MISSION_RESULT",
    "목록": "D2_CODEX_PAGE",
    "다음": "D2_CODEX_PAGE",
    "상세": "D2_STATUS_DETAIL",
    "골드": "D2_GOLD",
    "gold": "D2_GOLD",
    "g": "D2_GOLD",
    "포인트": "D2_GOLD",
    "point": "D2_GOLD",
    "points": "D2_GOLD",
    "잔액": "D2_GOLD",
    "내골드": "D2_GOLD",
    "p": "D2_GOLD",
    "pt": "D2_GOLD",
    "패스": "D2_PASS",
    "ticket": "D2_PASS",
    "tickets": "D2_PASS",
    "t": "D2_PASS",
    "도움말": "D2_HELP",
    "help": "D2_HELP",
    "?": "D2_HELP",
    "h": "D2_HELP",
    "리더보드": "D2_RANK",
    "랭킹": "D2_RANK",
    "leaderboard": "D2_RANK",
    "ranking": "D2_RANK",
    "l": "D2_RANK",
    "lb": "D2_RANK",
    "rank": "D2_RANK",
    "r": "D2_RANK",
}


def resolve_screen_for_command(command: str | None) -> ScreenDef:
    """명령어 문자열로 착지 화면을 결정. 미지 명령은 D0_HOME."""
    if not command:
        return D0_HOME
    key = command.strip().lower()
    # lower may break Korean but Korean is case-invariant; keep original too
    for candidate in (command.strip(), key):
        screen_id = _COMMAND_SCREEN_MAP.get(candidate)
        if screen_id:
            return _DEFAULT_REGISTRY.require(screen_id)
    # prefix matches for transfer etc.
    lower = command.strip().lower()
    if lower.startswith("골드주기") or lower.startswith("골드전송") or lower.startswith("pay ") or lower.startswith("send "):
        return D2_TRANSFER
    return D0_HOME
