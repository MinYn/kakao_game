"""
우주선 배지 관련 API 엔드포인트
"""
from datetime import datetime

from fastapi import APIRouter

from api.schemas import SpaceBadgeResponse
from space_badges import SpaceBadgeService, generate_svg


router = APIRouter(prefix="/api/space-badges", tags=["space-badges"])
service = SpaceBadgeService()


@router.get("/{user_id}", response_model=SpaceBadgeResponse)
def get_space_badge(user_id: str):
    """사용자 배지 조회 (DB 없이 결정적 랜덤)"""
    variant = service.get_variant_for_user(user_id)
    variant_index = service.find_variant_index(variant)
    svg_code = generate_svg(variant, variant_index, star_seed=service.stable_seed(user_id))
    now = datetime.utcnow()
    return SpaceBadgeResponse(
        user_id=user_id,
        name=variant.name,
        sub=variant.sub,
        shape=variant.shape.value,
        color=variant.color,
        svg=svg_code,
        created_at=now,
        updated_at=now,
    )
