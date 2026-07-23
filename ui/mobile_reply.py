"""모바일 온리 응답 빌더.

DETAIL = 15줄 × ≤25자 + 버튼 2
MENU   =  5줄 × ≤25자 + 버튼 4
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Optional, Sequence


MAX_LINE_CHARS = 25
MAX_LINES_DETAIL = 15
MAX_LINES_MENU = 5
BUTTONS_DETAIL = 2
BUTTONS_MENU = 4


class LayoutMode(str, Enum):
    DETAIL = "detail"
    MENU = "menu"

    @property
    def max_lines(self) -> int:
        return MAX_LINES_DETAIL if self is LayoutMode.DETAIL else MAX_LINES_MENU

    @property
    def button_count(self) -> int:
        return BUTTONS_DETAIL if self is LayoutMode.DETAIL else BUTTONS_MENU


@dataclass(frozen=True)
class MobileReply:
    """포맷된 모바일 응답."""

    text: str
    layout: LayoutMode
    buttons: List[dict]
    screen_id: str
    depth: int = 0

    def as_message(self) -> str:
        return self.text


def wrap_line(line: str, max_chars: int = MAX_LINE_CHARS) -> List[str]:
    """한 줄을 max_chars 이하로 분할. 공백 우선 분리, 없으면 강제 절단."""
    line = (line or "").rstrip()
    if not line:
        return []

    # 이미 짧으면 그대로
    if len(line) <= max_chars:
        return [line]

    parts: List[str] = []
    remaining = line
    while remaining:
        if len(remaining) <= max_chars:
            parts.append(remaining)
            break

        chunk = remaining[:max_chars]
        # 공백/구분자 기준으로 끊기
        break_at = -1
        for sep in (" ", "·", "/", ",", ":", "、", "…"):
            idx = chunk.rfind(sep)
            if idx >= max_chars // 3:
                break_at = max(break_at, idx + (0 if sep in ("·", "/", ",", ":", "、", "…") else 1))
        if break_at <= 0:
            # 공백 없음 → 강제 절단
            parts.append(chunk)
            remaining = remaining[max_chars:]
        else:
            parts.append(remaining[:break_at].rstrip())
            remaining = remaining[break_at:].lstrip()
    return [p for p in parts if p]


def fit_text(
    text: str,
    max_lines: int,
    max_chars: int = MAX_LINE_CHARS,
    *,
    allow_blank: bool = False,
) -> str:
    """텍스트를 줄 수·글자 수 제한에 맞게 정리.

    - 무의미한 빈 줄 패딩 금지 (allow_blank=False 기본)
    - 각 줄 len <= max_chars
    - 총 줄 수 <= max_lines (초과 시 절단, 마지막에 … 표시 가능)
    """
    if max_lines <= 0:
        return ""

    raw_lines = (text or "").split("\n")
    out: List[str] = []

    for raw in raw_lines:
        stripped = raw.rstrip()
        if not stripped.strip():
            if allow_blank and out and out[-1] != "":
                # 의도적 한 칸 공백은 허용하되 연속/패딩 금지
                if len(out) < max_lines:
                    out.append("")
            continue

        wrapped = wrap_line(stripped, max_chars)
        for part in wrapped:
            if len(out) >= max_lines:
                # 잘렸음을 표시 (자리 있으면)
                if out and not out[-1].endswith("…"):
                    last = out[-1]
                    if len(last) < max_chars:
                        out[-1] = (last + "…")[:max_chars]
                    else:
                        out[-1] = last[: max_chars - 1] + "…"
                return "\n".join(out)
            out.append(part[:max_chars])

    # trailing blank 제거
    while out and out[-1] == "":
        out.pop()

    return "\n".join(out[:max_lines])


def normalize_buttons(
    buttons: Sequence[dict],
    layout: LayoutMode,
) -> List[dict]:
    """버튼 개수를 레이아웃에 맞게 정확히 맞춤.

    - DETAIL: 정확히 2개
    - MENU: 정확히 4개
    부족하면 홈으로 채우고, 초과면 자른다.
    """
    required = layout.button_count
    cleaned: List[dict] = []
    seen: set[str] = set()

    for btn in buttons:
        if not btn:
            continue
        label = str(btn.get("label") or btn.get("messageText") or "").strip()
        message = str(btn.get("messageText") or btn.get("label") or "").strip()
        if not label or not message:
            continue
        # Discord 라벨 길이 여유
        label = label[:80]
        key = message.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"label": label, "messageText": message})
        if len(cleaned) >= required:
            break

    # 홈 폴백으로 채우기
    home = {"label": "🏠 홈", "messageText": "홈"}
    fillers = [
        home,
        {"label": "📊 상태", "messageText": "상태"},
        {"label": "🚀 출동", "messageText": "출동"},
        {"label": "🔨 성장", "messageText": "성장"},
    ]
    for filler in fillers:
        if len(cleaned) >= required:
            break
        key = filler["messageText"].lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(dict(filler))

    # 그래도 부족하면 번호 버튼
    i = 1
    while len(cleaned) < required:
        msg = f"홈"
        cleaned.append({"label": f"홈{i}", "messageText": msg})
        i += 1

    return cleaned[:required]


@dataclass
class MobileReplyBuilder:
    """화면 단위 모바일 응답 생성기."""

    max_line_chars: int = MAX_LINE_CHARS

    def build(
        self,
        lines: Iterable[str] | str,
        layout: LayoutMode,
        buttons: Sequence[dict],
        *,
        screen_id: str,
        depth: int = 0,
    ) -> MobileReply:
        if isinstance(lines, str):
            text_src = lines
        else:
            text_src = "\n".join(str(line) for line in lines if line is not None)

        text = fit_text(text_src, layout.max_lines, self.max_line_chars)
        normalized = normalize_buttons(buttons, layout)
        return MobileReply(
            text=text,
            layout=layout,
            buttons=normalized,
            screen_id=screen_id,
            depth=depth,
        )

    def build_menu(
        self,
        lines: Iterable[str] | str,
        buttons: Sequence[dict],
        *,
        screen_id: str,
        depth: int = 0,
    ) -> MobileReply:
        return self.build(lines, LayoutMode.MENU, buttons, screen_id=screen_id, depth=depth)

    def build_detail(
        self,
        lines: Iterable[str] | str,
        buttons: Sequence[dict],
        *,
        screen_id: str,
        depth: int = 0,
    ) -> MobileReply:
        return self.build(lines, LayoutMode.DETAIL, buttons, screen_id=screen_id, depth=depth)


def validate_reply(reply: MobileReply) -> List[str]:
    """레이아웃 위반 목록 반환 (비어 있으면 OK)."""
    errors: List[str] = []
    lines = reply.text.split("\n") if reply.text else []
    max_lines = reply.layout.max_lines
    if len(lines) > max_lines:
        errors.append(f"lines {len(lines)} > {max_lines}")
    for i, line in enumerate(lines):
        if len(line) > MAX_LINE_CHARS:
            errors.append(f"line {i} len {len(line)} > {MAX_LINE_CHARS}")
    expected_btns = reply.layout.button_count
    if len(reply.buttons) != expected_btns:
        errors.append(f"buttons {len(reply.buttons)} != {expected_btns}")
    if reply.depth < 0 or reply.depth > 3:
        errors.append(f"depth {reply.depth} out of 0..3")
    return errors
