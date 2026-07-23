"""모바일 전용 응답 레이아웃 (DETAIL / MENU + depth)."""

from ui.mobile_reply import (
    BUTTONS_DETAIL,
    BUTTONS_MENU,
    LayoutMode,
    MAX_LINE_CHARS,
    MAX_LINES_DETAIL,
    MAX_LINES_MENU,
    MobileReply,
    MobileReplyBuilder,
    fit_text,
    wrap_line,
)
from ui.screens import (
    ScreenDef,
    ScreenRegistry,
    get_screen,
    resolve_screen_for_command,
)

__all__ = [
    "BUTTONS_DETAIL",
    "BUTTONS_MENU",
    "LayoutMode",
    "MAX_LINE_CHARS",
    "MAX_LINES_DETAIL",
    "MAX_LINES_MENU",
    "MobileReply",
    "MobileReplyBuilder",
    "ScreenDef",
    "ScreenRegistry",
    "fit_text",
    "get_screen",
    "resolve_screen_for_command",
    "wrap_line",
]
