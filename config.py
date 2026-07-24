"""
설정 관리 모듈
"""
import os
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # 테스트/최소 환경에서 python-dotenv 없이도 동작
    pass


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
    

    # Redis 설정 (캐시/rate limit/idempotency/leaderboard)
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    USE_REDIS: bool = os.getenv('USE_REDIS', 'true').lower() == 'true'
    REDIS_RATE_LIMIT_PER_MINUTE: int = int(os.getenv('REDIS_RATE_LIMIT_PER_MINUTE', '120'))
    REDIS_IDEMPOTENCY_TTL_SECONDS: int = int(os.getenv('REDIS_IDEMPOTENCY_TTL_SECONDS', '86400'))
    REDIS_SOCKET_TIMEOUT_SECONDS: float = float(os.getenv('REDIS_SOCKET_TIMEOUT_SECONDS', '1.0'))
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

    # ---- 이슈 #19 Dopamine loop 튜닝 포인트 (코어 루프 상수) ----
    # 짧은 루프: 출동 → 결과 → 강화 유혹 → 재탭
    # 출동 실패 시 소형 보호 보상 (완전 무보상 금지)
    MISSION_FAIL_CONSOLATION_MIN: int = int(os.getenv('MISSION_FAIL_CONSOLATION_MIN', '3'))
    MISSION_FAIL_CONSOLATION_MAX: int = int(os.getenv('MISSION_FAIL_CONSOLATION_MAX', '8'))
    # 연속 출동 실패 soft pity (성공률 % 가산, 캡)
    MISSION_PITY_PER_FAIL: float = float(os.getenv('MISSION_PITY_PER_FAIL', '3.0'))
    MISSION_PITY_CAP: float = float(os.getenv('MISSION_PITY_CAP', '15.0'))
    # 연속 강화 실패 soft pity
    ENHANCE_PITY_PER_FAIL: float = float(os.getenv('ENHANCE_PITY_PER_FAIL', '2.0'))
    ENHANCE_PITY_CAP: float = float(os.getenv('ENHANCE_PITY_CAP', '12.0'))
    # 강화 마일스톤 본체 +N (연출 + 소형 골드)
    ENHANCE_MILESTONES: tuple = (5, 10, 15, 20, 25, 30)
    ENHANCE_MILESTONE_GOLD_BASE: int = int(os.getenv('ENHANCE_MILESTONE_GOLD_BASE', '25'))
    # 도감 중복 = 항상 보상 (등급별 골드)
    DUPLICATE_SHIP_GOLD: dict = {
        'F': 12, 'E': 18, 'D': 28, 'C': 45, 'B': 70, 'A': 120, 'S': 250,
    }
    # 일일 미니 목표 (홈 1줄)
    DAILY_MISSION_GOAL: int = int(os.getenv('DAILY_MISSION_GOAL', '5'))
    DAILY_ENHANCE_GOAL: int = int(os.getenv('DAILY_ENHANCE_GOAL', '3'))
    
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

