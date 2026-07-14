"""
SQLAlchemy 모델 정의
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from sqlalchemy.sql import func
from models.database import Base


class Gold(Base):
    """골드 테이블 모델"""
    __tablename__ = "gold"
    
    user_id = Column(String(255), primary_key=True)
    gold = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Gold(user_id='{self.user_id}', gold={self.gold})>"


class GoldHistory(Base):
    """골드 이력 테이블 모델"""
    __tablename__ = "gold_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_gold_history_user_id', 'user_id'),
        Index('idx_gold_history_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<GoldHistory(id={self.id}, user_id='{self.user_id}', amount={self.amount})>"


class BossTicket(Base):
    """보스몹 입장권 테이블 모델"""
    __tablename__ = "boss_tickets"
    
    user_id = Column(String(255), primary_key=True)
    tickets = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BossTicket(user_id='{self.user_id}', tickets={self.tickets})>"


class EnhancementLevel(Base):
    """강화 레벨 테이블 모델"""
    __tablename__ = "enhancement_levels"
    
    user_id = Column(String(255), primary_key=True)
    level = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<EnhancementLevel(user_id='{self.user_id}', level={self.level})>"


class GameStats(Base):
    """게임 통계 테이블 모델"""
    __tablename__ = "game_stats"
    
    user_id = Column(String(255), primary_key=True)
    enhancement_attempts = Column(Integer, nullable=False, default=0)
    enhancement_successes = Column(Integer, nullable=False, default=0)
    enhancement_failures = Column(Integer, nullable=False, default=0)
    hunt_normal = Column(Integer, nullable=False, default=0)
    hunt_special = Column(Integer, nullable=False, default=0)
    hunt_boss = Column(Integer, nullable=False, default=0)
    total_hunts = Column(Integer, nullable=False, default=0)
    total_hunt_reward = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GameStats(user_id='{self.user_id}', total_hunts={self.total_hunts})>"


class ShipCollection(Base):
    """우주선 수집 도감 테이블 모델"""
    __tablename__ = "ship_collection"

    user_id = Column(String(255), primary_key=True)
    ship_id = Column(String(100), primary_key=True)
    acquired_count = Column(Integer, nullable=False, default=1)
    first_acquired_at = Column(DateTime(timezone=True), server_default=func.now())
    last_acquired_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_ship_collection_user_id', 'user_id'),
    )

    def __repr__(self):
        return (
            f"<ShipCollection(user_id='{self.user_id}', "
            f"ship_id='{self.ship_id}', acquired_count={self.acquired_count})>"
        )
