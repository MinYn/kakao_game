"""
우주선 배지 관련 API 엔드포인트
"""
from datetime import datetime

from fastapi import APIRouter

from api.schemas import SpaceBadgeResponse
from gold_system_postgres import GoldSystemPostgres
from space_badges import SpaceBadgeService, generate_svg


router = APIRouter(prefix="/api/space-badges", tags=["space-badges"])
service = SpaceBadgeService()
gold_system = GoldSystemPostgres()


@router.get("/{user_id}", response_model=SpaceBadgeResponse)
def get_space_badge(user_id: str):
    """사용자 배지 조회. 저장된 기체 등급·본체 +N 을 SVG 에 반영."""
    variant = service.get_variant_for_user(user_id, offset=0)
    variant_index = service.find_variant_index(variant)
    progress = gold_system.get_ship_progress(user_id)
    grade = progress.grade.value
    body_enhance = progress.body_enhance
    upgrade_stage = service.upgrade_stage_from_body_enhance(body_enhance)
    svg_code = generate_svg(
        variant,
        variant_index,
        star_seed=service.stable_seed(user_id),
        upgrade_stage=upgrade_stage,
        grade=grade,
        body_enhance=body_enhance,
    )
    now = datetime.utcnow()
    return SpaceBadgeResponse(
        user_id=user_id,
        name=variant.name,
        sub=f"+{body_enhance}",
        shape=variant.shape.value,
        color=variant.color,
        svg=svg_code,
        created_at=now,
        updated_at=now,
    )
