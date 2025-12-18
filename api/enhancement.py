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
    """강화 레벨 설정"""
    level = db.query(EnhancementLevel).filter(EnhancementLevel.user_id == user_id).first()
    
    if level:
        level.level = max(0, level_update.level)
    else:
        level = EnhancementLevel(user_id=user_id, level=max(0, level_update.level))
        db.add(level)
    
    db.commit()
    db.refresh(level)
    return level
