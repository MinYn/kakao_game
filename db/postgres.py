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
                
                # 강화 레벨 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS enhancement_levels (
                        user_id VARCHAR(255) PRIMARY KEY,
                        level INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
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
