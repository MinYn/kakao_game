"""도파민 루프 계측 (이슈 #19).

최소 이벤트 셋:
  mission_result, enhance_result, ship_drop, button_click/screen_id, session_retap

Kafka 가 꺼져 있어도 구조화 로그로 수집 가능. 주간 튜닝용.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from config import Config

logger = logging.getLogger("telemetry")

# 세션 내 직전 루프 화면 (재탭률 추정)
_last_loop_by_user: Dict[str, str] = {}


def emit_telemetry(
    event_name: str,
    user_id: str,
    *,
    screen_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """텔레메트리 이벤트 발행. 항상 로그, 가능하면 Kafka game-events."""
    payload: Dict[str, Any] = {
        "type": f"telemetry.{event_name}",
        "event": event_name,
        "user_id": user_id,
        "screen_id": screen_id,
        "metadata": metadata or {},
        "ts": time.time(),
    }
    logger.info(
        "telemetry event=%s user=%s screen=%s meta=%s",
        event_name,
        user_id,
        screen_id,
        payload["metadata"],
    )

    if getattr(Config, "USE_KAFKA", False):
        try:
            from events.kafka_producer import publish_event
            from events.event_types import EventTopics

            publish_event(EventTopics.GAME_EVENTS, payload, key=user_id)
        except Exception as exc:  # pragma: no cover - 인프라 실패 무시
            logger.debug("telemetry kafka skip: %s", exc)

    return payload


def track_mission_result(
    user_id: str,
    *,
    success: bool,
    activity: str,
    reward: int = 0,
    screen_id: str = "D2_MISSION_RESULT",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta = {"success": success, "activity": activity, "reward": reward}
    if extra:
        meta.update(extra)
    _note_retap(user_id, "mission")
    return emit_telemetry("mission_result", user_id, screen_id=screen_id, metadata=meta)


def track_enhance_result(
    user_id: str,
    *,
    success: bool,
    margin: Optional[float] = None,
    celebration: Optional[str] = None,
    near_miss: bool = False,
    body_enhance: int = 0,
    screen_id: str = "D2_ENHANCE_RESULT",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {
        "success": success,
        "margin": margin,
        "celebration": celebration,
        "near_miss": near_miss,
        "body_enhance": body_enhance,
    }
    if extra:
        meta.update(extra)
    _note_retap(user_id, "enhance")
    return emit_telemetry("enhance_result", user_id, screen_id=screen_id, metadata=meta)


def track_ship_drop(
    user_id: str,
    *,
    grade: str,
    ship_id: str,
    is_new: bool,
    screen_id: str = "D2_MISSION_RESULT",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {
        "grade": grade,
        "ship_id": ship_id,
        "is_new": is_new,
    }
    if extra:
        meta.update(extra)
    return emit_telemetry("ship_drop", user_id, screen_id=screen_id, metadata=meta)


def track_screen(
    user_id: str,
    screen_id: str,
    *,
    command: str = "",
) -> Dict[str, Any]:
    return emit_telemetry(
        "button_click",
        user_id,
        screen_id=screen_id,
        metadata={"command": command},
    )


def _note_retap(user_id: str, loop: str) -> None:
    prev = _last_loop_by_user.get(user_id)
    if prev == loop:
        emit_telemetry(
            "session_retap",
            user_id,
            screen_id="",
            metadata={"loop": loop},
        )
    _last_loop_by_user[user_id] = loop


def reset_session_tracking(user_id: Optional[str] = None) -> None:
    """테스트용 세션 상태 초기화."""
    if user_id is None:
        _last_loop_by_user.clear()
    else:
        _last_loop_by_user.pop(user_id, None)
