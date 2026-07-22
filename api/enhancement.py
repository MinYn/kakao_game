"""
강화 레벨 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import EnhancementLevel
from api.schemas import (
    EnhancementLevelCreate, EnhancementLevelUpdate, EnhancementLevelResponse
)

router = APIRouter(prefix="/api/enhancement", tags=["enhancement"])


@router.get("/{user_id}", response_model=EnhancementLevelResponse)
def get_enhancement_level(user_id: str, db: Session = Depends(get_db)):
    """강화 레벨 조회"""
    level = db.query(EnhancementLevel).filter(EnhancementLevel.user_id == user_id).first()
    if not level:
        level = EnhancementLevel(user_id=user_id, level=0)
        db.add(level)
        db.commit()
        db.refresh(level)
    return level


@router.put("/{user_id}", response_model=EnhancementLevelResponse)
def set_enhancement_level(
    user_id: str,
    level_update: EnhancementLevelUpdate,
    db: Session = Depends(get_db)
):
    """본체 +N 설정. level 과 body_enhance 를 동기화 (레거시 API 호환)."""
    body = max(0, level_update.level)
    level = db.query(EnhancementLevel).filter(EnhancementLevel.user_id == user_id).first()

    if level:
        level.level = body
        if hasattr(level, "body_enhance"):
            level.body_enhance = body
        if hasattr(level, "ship_grade") and not level.ship_grade:
            level.ship_grade = "F"
    else:
        kwargs = {"user_id": user_id, "level": body}
        # SQLAlchemy 모델에 신규 컬럼이 있으면 함께 초기화
        if hasattr(EnhancementLevel, "body_enhance"):
            kwargs["body_enhance"] = body
        if hasattr(EnhancementLevel, "ship_grade"):
            kwargs["ship_grade"] = "F"
        level = EnhancementLevel(**kwargs)
        db.add(level)

    db.commit()
    db.refresh(level)
    return level
