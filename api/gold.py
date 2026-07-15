"""
골드 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import get_db
from models.models import Gold, GoldHistory
from api.schemas import (
    GoldCreate, GoldUpdate, GoldResponse,
    GoldHistoryCreate, GoldHistoryResponse,
    GoldTransferRequest, GoldTransferResponse,
    LeaderboardEntry, LeaderboardResponse
)
from events.kafka_producer import publish_event
from events.event_types import EventType, EventTopics, create_gold_event
from config import Config
from events.redis_runtime import RedisRuntime
import logging

logger = logging.getLogger(__name__)
_redis_runtime: RedisRuntime | None = None


def get_redis_runtime() -> RedisRuntime:
    global _redis_runtime
    if _redis_runtime is None:
        _redis_runtime = RedisRuntime()
    return _redis_runtime


def sync_gold_leaderboard(user_id: str, gold: int) -> None:
    if not Config.USE_REDIS:
        return
    try:
        get_redis_runtime().update_leaderboard(board="gold", user_id=user_id, score=gold)
    except Exception as exc:
        logger.warning("Redis leaderboard sync failed: user_id=%s error=%s", user_id, exc)


router = APIRouter(prefix="/api/gold", tags=["gold"])


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="조회 개수"),
    db: Session = Depends(get_db)
):
    """리더보드 조회. Redis Sorted Set을 우선 사용하고 장애/미스 시 DB로 대체한다."""
    total = db.query(Gold).count()

    if Config.USE_REDIS:
        try:
            cached_entries = get_redis_runtime().get_leaderboard(board="gold", limit=limit)
            if cached_entries:
                return LeaderboardResponse(
                    entries=[
                        LeaderboardEntry(user_id=entry.user_id, gold=entry.score, rank=entry.rank)
                        for entry in cached_entries
                    ],
                    total=total,
                )
        except Exception as exc:
            logger.warning("Redis leaderboard read failed; falling back to DB: %s", exc)

    golds = db.query(Gold)\
        .order_by(Gold.gold.desc())\
        .limit(limit)\
        .all()

    entries = [
        LeaderboardEntry(user_id=g.user_id, gold=g.gold, rank=idx + 1)
        for idx, g in enumerate(golds)
    ]

    for entry in entries:
        sync_gold_leaderboard(entry.user_id, entry.gold)

    return LeaderboardResponse(entries=entries, total=total)

@router.get("/{user_id}", response_model=GoldResponse)
def get_gold(user_id: str, db: Session = Depends(get_db)):
    """사용자 골드 조회"""
    gold = db.query(Gold).filter(Gold.user_id == user_id).first()
    if not gold:
        # 신규 사용자 생성
        gold = Gold(user_id=user_id, gold=0)
        db.add(gold)
        db.commit()
        db.refresh(gold)
    return gold


@router.post("/{user_id}/add", response_model=GoldResponse)
def add_gold(
    user_id: str,
    amount: int = Query(..., gt=0, description="추가할 골드"),
    reason: Optional[str] = Query(None, description="추가 사유"),
    db: Session = Depends(get_db)
):
    """골드 추가"""
    gold = db.query(Gold).filter(Gold.user_id == user_id).first()
    
    if gold:
        gold.gold += amount
    else:
        gold = Gold(user_id=user_id, gold=amount)
        db.add(gold)
    
    # 이력 기록
    if reason:
        history = GoldHistory(user_id=user_id, amount=amount, reason=reason)
        db.add(history)
    
    db.commit()
    db.refresh(gold)
    sync_gold_leaderboard(user_id, gold.gold)
    
    # Kafka 이벤트 발행
    if Config.USE_KAFKA:
        event = create_gold_event(
            EventType.GOLD_ADDED,
            user_id,
            amount,
            reason or "",
            {'new_balance': gold.gold}
        )
        publish_event(EventTopics.GOLD_EVENTS, event, key=user_id)
    
    return gold


@router.post("/{user_id}/deduct", response_model=GoldResponse)
def deduct_gold(
    user_id: str,
    amount: int = Query(..., gt=0, description="차감할 골드"),
    reason: Optional[str] = Query(None, description="차감 사유"),
    db: Session = Depends(get_db)
):
    """골드 차감"""
    gold = db.query(Gold).filter(Gold.user_id == user_id).first()
    
    if not gold or gold.gold < amount:
        raise HTTPException(status_code=400, detail="골드가 부족합니다")
    
    gold.gold -= amount
    
    # 이력 기록
    if reason:
        history = GoldHistory(user_id=user_id, amount=-amount, reason=reason)
        db.add(history)
    
    db.commit()
    db.refresh(gold)
    sync_gold_leaderboard(user_id, gold.gold)
    
    # Kafka 이벤트 발행
    if Config.USE_KAFKA:
        event = create_gold_event(
            EventType.GOLD_DEDUCTED,
            user_id,
            amount,
            reason or "",
            {'new_balance': gold.gold}
        )
        publish_event(EventTopics.GOLD_EVENTS, event, key=user_id)
    
    return gold


@router.put("/{user_id}", response_model=GoldResponse)
def set_gold(
    user_id: str,
    gold_update: GoldUpdate,
    db: Session = Depends(get_db)
):
    """골드 설정 (절대값)"""
    gold = db.query(Gold).filter(Gold.user_id == user_id).first()
    
    if gold:
        gold.gold = gold_update.gold
    else:
        gold = Gold(user_id=user_id, gold=gold_update.gold)
        db.add(gold)
    
    db.commit()
    db.refresh(gold)
    sync_gold_leaderboard(user_id, gold.gold)
    return gold


@router.post("/transfer", response_model=GoldTransferResponse)
def transfer_gold(
    transfer: GoldTransferRequest,
    db: Session = Depends(get_db)
):
    """골드 전송"""
    if transfer.from_user == transfer.to_user:
        raise HTTPException(status_code=400, detail="자기 자신에게 전송할 수 없습니다")
    
    from_gold = db.query(Gold).filter(Gold.user_id == transfer.from_user).first()
    if not from_gold or from_gold.gold < transfer.amount:
        raise HTTPException(status_code=400, detail="골드가 부족합니다")
    
    to_gold = db.query(Gold).filter(Gold.user_id == transfer.to_user).first()
    
    # 차감
    from_gold.gold -= transfer.amount
    
    # 추가
    if to_gold:
        to_gold.gold += transfer.amount
    else:
        to_gold = Gold(user_id=transfer.to_user, gold=transfer.amount)
        db.add(to_gold)
    
    # 이력 기록
    reason = transfer.reason or "사용자 간 골드 전송"
    from_history = GoldHistory(
        user_id=transfer.from_user,
        amount=-transfer.amount,
        reason=f"골드 전송 → {transfer.to_user}: {reason}"
    )
    to_history = GoldHistory(
        user_id=transfer.to_user,
        amount=transfer.amount,
        reason=f"골드 수신 ← {transfer.from_user}: {reason}"
    )
    db.add(from_history)
    db.add(to_history)
    
    db.commit()
    db.refresh(from_gold)
    db.refresh(to_gold)
    sync_gold_leaderboard(transfer.from_user, from_gold.gold)
    sync_gold_leaderboard(transfer.to_user, to_gold.gold)
    
    # Kafka 이벤트 발행
    if Config.USE_KAFKA:
        event = create_gold_event(
            EventType.GOLD_TRANSFERRED,
            transfer.from_user,
            transfer.amount,
            reason,
            {
                'to_user': transfer.to_user,
                'from_balance': from_gold.gold,
                'to_balance': to_gold.gold
            }
        )
        publish_event(EventTopics.GOLD_EVENTS, event, key=transfer.from_user)
    
    return GoldTransferResponse(
        success=True,
        from_user_balance=from_gold.gold,
        to_user_balance=to_gold.gold,
        message="골드 전송 완료"
    )


@router.get("/{user_id}/history", response_model=List[GoldHistoryResponse])
def get_gold_history(
    user_id: str,
    limit: int = Query(10, ge=1, le=100, description="조회 개수"),
    db: Session = Depends(get_db)
):
    """골드 이력 조회"""
    history = db.query(GoldHistory)\
        .filter(GoldHistory.user_id == user_id)\
        .order_by(GoldHistory.created_at.desc())\
        .limit(limit)\
        .all()
    return history


