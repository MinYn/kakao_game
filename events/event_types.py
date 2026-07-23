"""
이벤트 타입 정의
"""
from enum import Enum
from typing import Dict, Any


class EventType(str, Enum):
    """이벤트 타입"""
    GOLD_ADDED = "gold.added"
    GOLD_DEDUCTED = "gold.deducted"
    GOLD_TRANSFERRED = "gold.transferred"
    GAME_STARTED = "game.started"
    GAME_ENDED = "game.ended"
    GAME_ACTION = "game.action"
    STATS_UPDATED = "stats.updated"
    # 이슈 #19 도파민 루프 계측
    MISSION_RESULT = "telemetry.mission_result"
    ENHANCE_RESULT = "telemetry.enhance_result"
    SHIP_DROP = "telemetry.ship_drop"
    BUTTON_CLICK = "telemetry.button_click"
    SESSION_RETAP = "telemetry.session_retap"


class EventTopics:
    """Kafka 토픽 이름"""
    GOLD_EVENTS = "gold-events"
    GAME_EVENTS = "game-events"
    STATS_EVENTS = "stats-events"


def create_gold_event(
    event_type: EventType,
    user_id: str,
    amount: int,
    reason: str = "",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """골드 이벤트 생성"""
    return {
        'type': event_type.value,
        'user_id': user_id,
        'amount': amount,
        'reason': reason,
        'metadata': metadata or {},
        'timestamp': None  # Kafka가 자동으로 추가
    }


def create_game_event(
    event_type: EventType,
    user_id: str,
    game_type: str,
    action: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """게임 이벤트 생성"""
    return {
        'type': event_type.value,
        'user_id': user_id,
        'game_type': game_type,
        'action': action,
        'metadata': metadata or {},
        'timestamp': None
    }


def create_stats_event(
    user_id: str,
    stats_type: str,
    stats_data: Dict[str, Any]
) -> Dict[str, Any]:
    """통계 이벤트 생성"""
    return {
        'type': EventType.STATS_UPDATED.value,
        'user_id': user_id,
        'stats_type': stats_type,
        'stats_data': stats_data,
        'timestamp': None
    }
