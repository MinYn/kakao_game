"""
PostgreSQL 데이터베이스 연결 및 관리
"""
import os
from contextlib import contextmanager
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from config import Config


class PostgreSQLManager:
    """PostgreSQL 연결 풀 관리"""
    
    _pool: Optional[ThreadedConnectionPool] = None
    
    @classmethod
    def initialize(cls):
        """연결 풀 초기화"""
        if cls._pool is None:
            db_config = {
                'host': Config.POSTGRES_HOST,
                'port': Config.POSTGRES_PORT,
                'database': Config.POSTGRES_DB,
                'user': Config.POSTGRES_USER,
                'password': Config.POSTGRES_PASSWORD,
                'minconn': 1,
                'maxconn': 10,
            }
            cls._pool = ThreadedConnectionPool(**db_config)
            cls._init_schema()
    
    @classmethod
    def _init_schema(cls):
        """데이터베이스 스키마 초기화"""
        with cls.get_connection() as conn:
            with conn.cursor() as cursor:
                # 골드 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gold (
                        user_id VARCHAR(255) PRIMARY KEY,
                        gold INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 골드 이력 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gold_history (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        amount INTEGER NOT NULL,
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 인덱스 생성
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_gold_history_user_id 
                    ON gold_history(user_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_gold_history_created_at 
                    ON gold_history(created_at DESC)
                ''')
                
                # 보스몹 입장권 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS boss_tickets (
                        user_id VARCHAR(255) PRIMARY KEY,
                        tickets INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 강화 레벨 테이블 (기체 등급/본체+N/파츠+N)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS enhancement_levels (
                        user_id VARCHAR(255) PRIMARY KEY,
                        level INTEGER NOT NULL DEFAULT 0,
                        ship_grade VARCHAR(8) NOT NULL DEFAULT 'F',
                        body_enhance INTEGER NOT NULL DEFAULT 0,
                        equipped_ship_id VARCHAR(100),
                        part_engine INTEGER NOT NULL DEFAULT 0,
                        part_sensor INTEGER NOT NULL DEFAULT 0,
                        part_armor INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cls._ensure_enhancement_columns(cursor)
                
                # 게임 통계 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_stats (
                        user_id VARCHAR(255) PRIMARY KEY,
                        enhancement_attempts INTEGER NOT NULL DEFAULT 0,
                        enhancement_successes INTEGER NOT NULL DEFAULT 0,
                        enhancement_failures INTEGER NOT NULL DEFAULT 0,
                        hunt_normal INTEGER NOT NULL DEFAULT 0,
                        hunt_special INTEGER NOT NULL DEFAULT 0,
                        hunt_boss INTEGER NOT NULL DEFAULT 0,
                        total_hunts INTEGER NOT NULL DEFAULT 0,
                        total_hunt_reward INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 우주선 수집 도감 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ship_collection (
                        user_id VARCHAR(255) NOT NULL,
                        ship_id VARCHAR(100) NOT NULL,
                        acquired_count INTEGER NOT NULL DEFAULT 1,
                        first_acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, ship_id)
                    )
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_ship_collection_user_id
                    ON ship_collection(user_id)
                ''')
                
                conn.commit()

    @classmethod
    def _ensure_enhancement_columns(cls, cursor) -> None:
        """기존 enhancement_levels 에 신규 컬럼을 추가하고 level 을 1회 이전."""
        columns = {
            "ship_grade": "VARCHAR(8) NOT NULL DEFAULT 'F'",
            "body_enhance": "INTEGER NOT NULL DEFAULT 0",
            "equipped_ship_id": "VARCHAR(100)",
            "part_engine": "INTEGER NOT NULL DEFAULT 0",
            "part_sensor": "INTEGER NOT NULL DEFAULT 0",
            "part_armor": "INTEGER NOT NULL DEFAULT 0",
        }
        body_column_added = False
        for column, definition in columns.items():
            cursor.execute(
                '''
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'enhancement_levels'
                  AND column_name = %s
                ''',
                (column,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    f"ALTER TABLE enhancement_levels ADD COLUMN {column} {definition}"
                )
                if column == "body_enhance":
                    body_column_added = True
        # 레거시 → 신규 복사는 body_enhance 컬럼을 방금 추가한 최초 1회만 수행한다.
        # 이후에는 body_enhance 가 원본이고 level 은 하위 호환 mirror 이다.
        if body_column_added:
            cursor.execute(
                '''
                UPDATE enhancement_levels
                SET body_enhance = GREATEST(COALESCE(level, 0), 0),
                    ship_grade = COALESCE(NULLIF(ship_grade, ''), 'F')
                '''
            )
        cursor.execute(
            '''
            UPDATE enhancement_levels
            SET ship_grade = COALESCE(NULLIF(ship_grade, ''), 'F')
            '''
        )
        cursor.execute(
            '''
            UPDATE enhancement_levels
            SET level = GREATEST(COALESCE(body_enhance, 0), 0)
            WHERE COALESCE(level, 0) <> COALESCE(body_enhance, 0)
            '''
        )
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """연결 풀에서 연결 가져오기 (컨텍스트 매니저)"""
        if cls._pool is None:
            cls.initialize()
        
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)
    
    @classmethod
    def close(cls):
        """연결 풀 종료"""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
