"""
SQLAlchemy 데이터베이스 설정
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config

# 데이터베이스 URL 생성
DATABASE_URL = (
    f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}"
    f"@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_size=10,
    max_overflow=20,
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    Base.metadata.create_all(bind=engine)
