"""
Pydantic 스키마 정의 (API 요청/응답 모델)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Gold 관련 스키마
class GoldBase(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    gold: int = Field(0, ge=0, description="골드 수량")


class GoldCreate(GoldBase):
    pass


class GoldUpdate(BaseModel):
    gold: int = Field(..., ge=0, description="골드 수량")


class GoldResponse(GoldBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Gold History 관련 스키마
class GoldHistoryBase(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    amount: int = Field(..., description="변동 금액")
    reason: Optional[str] = Field(None, description="변동 사유")


class GoldHistoryCreate(GoldHistoryBase):
    pass


class GoldHistoryResponse(GoldHistoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Gold Transfer 스키마
class GoldTransferRequest(BaseModel):
    from_user: str = Field(..., description="보낸 사용자 ID")
    to_user: str = Field(..., description="받은 사용자 ID")
    amount: int = Field(..., gt=0, description="전송 금액")
    reason: Optional[str] = Field(None, description="전송 사유")


class GoldTransferResponse(BaseModel):
    success: bool
    from_user_balance: int
    to_user_balance: int
    message: str


# Boss Ticket 관련 스키마
class BossTicketBase(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    tickets: int = Field(0, ge=0, description="입장권 수량")


class BossTicketCreate(BossTicketBase):
    pass


class BossTicketUpdate(BaseModel):
    tickets: int = Field(..., ge=0, description="입장권 수량")


class BossTicketResponse(BossTicketBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Enhancement Level 관련 스키마
class EnhancementLevelBase(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    level: int = Field(0, ge=0, description="강화 레벨")


class EnhancementLevelCreate(EnhancementLevelBase):
    pass


class EnhancementLevelUpdate(BaseModel):
    level: int = Field(..., ge=0, description="강화 레벨")


class EnhancementLevelResponse(EnhancementLevelBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Game Stats 관련 스키마
class GameStatsBase(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    enhancement_attempts: int = Field(0, ge=0)
    enhancement_successes: int = Field(0, ge=0)
    enhancement_failures: int = Field(0, ge=0)
    hunt_normal: int = Field(0, ge=0)
    hunt_special: int = Field(0, ge=0)
    hunt_boss: int = Field(0, ge=0)
    total_hunts: int = Field(0, ge=0)
    total_hunt_reward: int = Field(0, ge=0)


class GameStatsCreate(GameStatsBase):
    pass


class GameStatsUpdate(BaseModel):
    enhancement_attempts: Optional[int] = Field(None, ge=0)
    enhancement_successes: Optional[int] = Field(None, ge=0)
    enhancement_failures: Optional[int] = Field(None, ge=0)
    hunt_normal: Optional[int] = Field(None, ge=0)
    hunt_special: Optional[int] = Field(None, ge=0)
    hunt_boss: Optional[int] = Field(None, ge=0)
    total_hunts: Optional[int] = Field(None, ge=0)
    total_hunt_reward: Optional[int] = Field(None, ge=0)


class GameStatsResponse(GameStatsBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Leaderboard 스키마
class LeaderboardEntry(BaseModel):
    user_id: str
    gold: int
    rank: int


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total: int
