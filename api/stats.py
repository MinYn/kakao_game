"""
게임 통계 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import GameStats
from api.schemas import GameStatsCreate, GameStatsUpdate, GameStatsResponse
from events.kafka_producer import publish_event
from events.event_types import EventTopics, create_stats_event
from config import Config

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/{user_id}", response_model=GameStatsResponse)
def get_game_stats(user_id: str, db: Session = Depends(get_db)):
    """게임 통계 조회"""
    stats = db.query(GameStats).filter(GameStats.user_id == user_id).first()
    if not stats:
        stats = GameStats(user_id=user_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


@router.post("/{user_id}", response_model=GameStatsResponse)
def create_game_stats(
    user_id: str,
    stats_create: GameStatsCreate,
    db: Session = Depends(get_db)
):
    """게임 통계 생성"""
    stats = db.query(GameStats).filter(GameStats.user_id == user_id).first()
    
    if stats:
        # 기존 통계 업데이트
        for field, value in stats_create.dict(exclude={'user_id'}).items():
            setattr(stats, field, value)
    else:
        stats = GameStats(**stats_create.dict())
        db.add(stats)
    
    db.commit()
    db.refresh(stats)
    
    # Kafka 이벤트 발행
    if Config.USE_KAFKA:
        event = create_stats_event(
            user_id,
            'game_stats',
            stats_create.dict(exclude={'user_id'})
        )
        publish_event(EventTopics.STATS_EVENTS, event, key=user_id)
    
    return stats


@router.patch("/{user_id}", response_model=GameStatsResponse)
def update_game_stats(
    user_id: str,
    stats_update: GameStatsUpdate,
    db: Session = Depends(get_db)
):
    """게임 통계 업데이트 (증가값)"""
    stats = db.query(GameStats).filter(GameStats.user_id == user_id).first()
    
    if not stats:
        # 기본값으로 생성
        stats = GameStats(user_id=user_id)
        db.add(stats)
    
    # 증가값으로 업데이트
    update_data = stats_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        current_value = getattr(stats, field, 0)
        setattr(stats, field, current_value + value)
    
    db.commit()
    db.refresh(stats)
    
    # Kafka 이벤트 발행
    if Config.USE_KAFKA:
        event = create_stats_event(
            user_id,
            'game_stats',
            update_data
        )
        publish_event(EventTopics.STATS_EVENTS, event, key=user_id)
    
    return stats


@router.put("/{user_id}", response_model=GameStatsResponse)
def set_game_stats(
    user_id: str,
    stats_update: GameStatsUpdate,
    db: Session = Depends(get_db)
):
    """게임 통계 설정 (절대값)"""
    stats = db.query(GameStats).filter(GameStats.user_id == user_id).first()
    
    if stats:
        # 기존 값 유지하거나 새 값으로 업데이트
        update_data = stats_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(stats, field, value)
    else:
        # 기본값으로 생성
        stats = GameStats(user_id=user_id)
        update_data = stats_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(stats, field, value)
        db.add(stats)
    
    db.commit()
    db.refresh(stats)
    return stats
