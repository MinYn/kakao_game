# PostgreSQL + Kafka 설정 가이드

## 개요

PostgreSQL + Kafka 기반 게임봇 시스템 설정 가이드입니다.

## 아키텍처

- PostgreSQL: 안정적인 관계형 데이터베이스
- Kafka: 메시징 큐를 통한 비동기 이벤트 처리
- 수평 확장 가능
- 이벤트 기반 아키텍처

## 시작하기

### 1. 환경 설정

`.env` 파일에 다음 설정 추가:

```env
# PostgreSQL 설정
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kakao_game
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Kafka 설정
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
USE_KAFKA=true
```

### 2. Docker Compose로 인프라 실행

```bash
docker-compose up -d
```

이 명령어로 다음 서비스들이 시작됩니다:
- PostgreSQL (포트 5432)
- Zookeeper (Kafka 의존성)
- Kafka (포트 9092)
- 게임봇 메인 서버 (포트 5000)
- Kafka 이벤트 워커

### 3. 코드 변경

`game_engine.py`는 이미 `GoldSystemPostgres`를 사용하도록 변경되었습니다.

## 주요 변경사항

### 1. 골드 시스템 (`gold_system_postgres.py`)

- PostgreSQL 연결 풀 사용
- 모든 골드 트랜잭션이 Kafka 이벤트로 발행됨
- 비동기 처리 가능

### 2. 이벤트 시스템 (`events/`)

- `kafka_producer.py`: 이벤트 발행
- `event_types.py`: 이벤트 타입 정의
- 골드 이벤트, 게임 이벤트, 통계 이벤트

### 3. 워커 (`workers/event_consumer.py`)

- Kafka 컨슈머로 이벤트 처리
- 비동기 작업 수행 (알림, 분석 등)

## 운영 방법

### 서비스 시작

```bash
# 전체 스택 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만
docker-compose logs -f gamebot
docker-compose logs -f worker
```

### 서비스 중지

```bash
docker-compose down
```

### 데이터 백업

```bash
# PostgreSQL 백업
docker-compose exec postgres pg_dump -U postgres kakao_game > backup.sql

# 복원
docker-compose exec -T postgres psql -U postgres kakao_game < backup.sql
```

## Kafka 토픽 확인

```bash
# 토픽 목록 확인
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# 토픽 메시지 확인
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic gold-events \
  --from-beginning
```

## 장점

1. **확장성**: 여러 인스턴스 실행 가능
2. **안정성**: PostgreSQL의 트랜잭션 보장
3. **비동기 처리**: Kafka를 통한 이벤트 기반 아키텍처
4. **모니터링**: 이벤트 스트림을 통한 분석 가능
5. **장애 복구**: Kafka의 메시지 보존으로 재처리 가능

## 주의사항

- Kafka는 기본적으로 메시지를 보존하므로 디스크 공간 관리 필요
- PostgreSQL 연결 풀 크기 조정 필요 (트래픽에 따라)
- Kafka 토픽 파티션 수는 동시 처리량에 따라 조정

## 문제 해결

### PostgreSQL 연결 실패
- `POSTGRES_HOST` 환경변수 확인
- Docker 네트워크 확인: `docker network inspect kakao_game_gamebot-network`

### Kafka 연결 실패
- `KAFKA_BOOTSTRAP_SERVERS` 확인
- Kafka 컨테이너 상태 확인: `docker-compose ps kafka`

### 워커가 이벤트를 처리하지 않음
- 워커 로그 확인: `docker-compose logs worker`
- Kafka 토픽에 메시지가 있는지 확인
