"""
설정 관리 모듈
"""
import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """설정 클래스"""
    
    # 플랫폼 설정
    PLATFORM: str = os.getenv('PLATFORM', 'discord')
    
    # 디스코드 설정
    DISCORD_TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
    DISCORD_COMMAND_PREFIX: str = os.getenv('DISCORD_COMMAND_PREFIX', '!')
    
    # 골드 시스템 설정
    DATA_FILE: str = os.getenv('DATA_FILE', 'data.db')
    INITIAL_GOLD: int = int(os.getenv('INITIAL_GOLD', '100'))
    
    # PostgreSQL 설정
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'kakao_game')
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'postgres')
    
    # Kafka 설정
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    USE_KAFKA: bool = os.getenv('USE_KAFKA', 'true').lower() == 'true'
    KAFKA_INCOMING_TOPIC: str = os.getenv('KAFKA_INCOMING_TOPIC', 'platform.incoming')
    KAFKA_OUTGOING_TOPIC: str = os.getenv('KAFKA_OUTGOING_TOPIC', 'platform.outgoing')
    KAFKA_PLATFORM_GROUP: str = os.getenv('KAFKA_PLATFORM_GROUP', 'platform-router')
    
    # 게임 설정 - 숫자맞추기
    NUMBER_GUESS_ENTRY_COST: int = int(os.getenv('NUMBER_GUESS_ENTRY_COST', '10'))
    NUMBER_GUESS_BASE_REWARD: int = int(os.getenv('NUMBER_GUESS_BASE_REWARD', '50'))
    NUMBER_GUESS_BONUS_PER_ATTEMPT: int = int(os.getenv('NUMBER_GUESS_BONUS_PER_ATTEMPT', '5'))
    NUMBER_GUESS_CONSOLATION: int = int(os.getenv('NUMBER_GUESS_CONSOLATION', '5'))
    
    # 게임 설정 - 가위바위보
    RPS_WIN_REWARD: int = int(os.getenv('RPS_WIN_REWARD', '10'))
    RPS_LOSE_COST: int = int(os.getenv('RPS_LOSE_COST', '5'))
    
    # 게임 설정 - 강화
    ENHANCEMENT_MAX_LEVEL: int = int(os.getenv('ENHANCEMENT_MAX_LEVEL', '15'))
    ENHANCEMENT_BASE_COST: int = int(os.getenv('ENHANCEMENT_BASE_COST', '40'))  # 기본 비용 감소
    ENHANCEMENT_COST_MULTIPLIER: float = float(os.getenv('ENHANCEMENT_COST_MULTIPLIER', '1.4'))  # 비용 증가율 완화
    ENHANCEMENT_SELL_MULTIPLIER: float = float(os.getenv('ENHANCEMENT_SELL_MULTIPLIER', '0.6'))  # 판매 가격 배율 증가
    ENHANCEMENT_LEVEL_BONUS: int = int(os.getenv('ENHANCEMENT_LEVEL_BONUS', '40'))  # 레벨당 보너스 증가
    
    # 게임 설정 - 몬스터 사냥
    MONSTER_HUNT_REWARD_MULTIPLIER: float = float(os.getenv('MONSTER_HUNT_REWARD_MULTIPLIER', '0.1'))  # 레벨당 보상 배율 (10%)
    BOSS_TICKET_DROP_RATE: float = float(os.getenv('BOSS_TICKET_DROP_RATE', '0.3'))  # 특수몹 사냥 시 보스몹 입장권 드랍 확률 (30%)
    
    # 서버 설정
    SERVER_HOST: str = os.getenv('SERVER_HOST', '0.0.0.0')
    SERVER_PORT: int = int(os.getenv('SERVER_PORT', '5000'))
    EXTERNAL_PORT: int = int(os.getenv('EXTERNAL_PORT', '8080'))  # 외부 노출 포트
    USE_NGINX: bool = os.getenv('USE_NGINX', 'true').lower() == 'true'  # Nginx 사용 여부
    GUNICORN_WORKERS: int = int(os.getenv('GUNICORN_WORKERS', '4'))  # Gunicorn 워커 수
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('LOG_FILE')
    
    @classmethod
    def validate(cls) -> bool:
        """설정 유효성 검사"""
        # 카카오톡은 웹훅 서버 방식 사용으로 API 키 불필요
        if cls.PLATFORM == 'discord' and not cls.DISCORD_TOKEN:
            print("⚠️ 경고: DISCORD_TOKEN이 설정되지 않았습니다.")
            return False
        
        return True

