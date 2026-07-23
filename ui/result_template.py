"""DETAIL 결과 연출 템플릿 (이슈 #19 DDD).

슬롯 고정 순서:
  훅 → 수치 변화 → 보너스/드랍 → 진행(비용·성공률) → 한 번 더(CTA 문구)

#17 상한: 15줄 × ≤25자. 이 모듈은 슬롯만 조립하고 fit 은 MobileReplyBuilder 가 담당.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence


# 코어 루프 상수 문서화 (코드·문서 동기화용)
CORE_LOOP_SHORT = "출동 → 성공/실패/득템/기체? → 골드↑ → 강화 유혹 → 재탭"
CORE_LOOP_MID = "+N 구간 돌파 · 등급 승급 임박 · 도감 빈칸"
CORE_LOOP_LONG = "F→S · 파츠 +N · 배지 티어"

# 이모지 톤 통일 (이슈 #19)
EMOJI = {
    "success": "✅",
    "fail": "❌",
    "near_miss": "⚠️",
    "loot": "🎁",
    "up": "⬆️",
    "celebrate": "💥",
    "new": "🆕",
    "pity": "🛡️",
    "daily": "📅",
    "mission": "🚀",
    "enhance": "🔨",
}


def build_detail_slots(
    *,
    hook: str,
    metrics: Sequence[str] = (),
    bonus: Sequence[str] = (),
    progress: Sequence[str] = (),
    cta: Optional[str] = None,
    max_lines: int = 15,
) -> List[str]:
    """훅→수치→보너스→진행→CTA 슬롯을 순서대로 이어 붙인다.

    빈 슬롯은 생략. 총 줄 수가 max_lines 를 넘으면 뒤에서부터 자른다
    (훅·수치 우선, CTA 가 남도록 중간 보너스부터 축소).
    """
    sections: List[List[str]] = []
    if hook:
        sections.append([hook])
    metrics_lines = [m for m in metrics if m]
    if metrics_lines:
        sections.append(list(metrics_lines))
    bonus_lines = [b for b in bonus if b]
    if bonus_lines:
        sections.append(list(bonus_lines))
    progress_lines = [p for p in progress if p]
    if progress_lines:
        sections.append(list(progress_lines))
    if cta:
        sections.append([cta])

    flat: List[str] = []
    for sec in sections:
        flat.extend(sec)

    if len(flat) <= max_lines:
        return flat

    # 우선순위: hook(0) > metrics(1) > progress > cta > bonus 축소
    # 단순 전략: 보너스 슬롯부터 줄이고, 그래도 넘치면 중간 절단
    if bonus_lines and len(sections) >= 3:
        # rebuild without trailing bonus lines until fit
        keep_bonus = list(bonus_lines)
        while keep_bonus and _flat_len(sections, bonus_override=keep_bonus) > max_lines:
            keep_bonus.pop()
        return _flatten(sections, bonus_override=keep_bonus)[:max_lines]

    return flat[:max_lines]


def _flat_len(sections: Sequence[Sequence[str]], bonus_override: Optional[Sequence[str]] = None) -> int:
    return len(_flatten(sections, bonus_override=bonus_override))


def _flatten(
    sections: Sequence[Sequence[str]],
    bonus_override: Optional[Sequence[str]] = None,
) -> List[str]:
    out: List[str] = []
    # sections layout assumed: [hook], [metrics], [bonus?], [progress?], [cta?]
    # We only override the first section that looks like the original bonus if provided.
    # Safer: rebuild from known indices when caller used build_detail_slots structure.
    if bonus_override is None:
        for sec in sections:
            out.extend(sec)
        return out

    # Replace the bonus section (index 2 when hook+metrics present) if length matches pattern
    for i, sec in enumerate(sections):
        if i == 2 and bonus_override is not None:
            out.extend(bonus_override)
        else:
            out.extend(sec)
    return out


def loop_cta_buttons(
    *,
    primary_label: str,
    primary_message: str,
    secondary_label: str,
    secondary_message: str,
) -> List[dict]:
    """D2 루프 유지용 버튼 2개 (홈 강제 없음 — 이슈 #19 CTA 우선)."""
    return [
        {"label": primary_label[:80], "messageText": primary_message},
        {"label": secondary_label[:80], "messageText": secondary_message},
    ]
