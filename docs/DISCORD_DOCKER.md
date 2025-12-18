# Discord 봇 Docker 설정 가이드

## 개요

Discord 봇을 Docker 컨테이너로 실행하는 방법입니다.

## 사전 요구사항

1. Discord 봇 토큰 필요
2. Docker 및 Docker Compose 설치

## 설정 방법

### 1. Discord 봇 토큰 설정

`.env` 파일에 Discord 토큰 추가:

```env
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_COMMAND_PREFIX=!
```

### 2. Discord 봇만 실행

```bash
# Discord 봇만 시작
docker-compose up -d discord

# 로그 확인
docker-compose logs -f discord
```

### 3. 전체 스택 실행 (Kakao + Discord)

```bash
# 모든 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d postgres kafka discord
```

## 서비스 구성

### Discord 서비스

- **컨테이너 이름**: `kakao_game_discord`
- **명령어**: `python main.py discord`
- **의존성**: PostgreSQL, Kafka
- **네트워크**: `gamebot-network`

### 환경 변수

Discord 봇에 필요한 환경 변수:

```env
PLATFORM=discord
DISCORD_TOKEN=your_token
DISCORD_COMMAND_PREFIX=!
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

## 사용 방법

### 서비스 시작

```bash
# Discord 봇 시작
docker-compose up -d discord

# 상태 확인
docker-compose ps discord

# 로그 확인
docker-compose logs -f discord
```

### 서비스 중지

```bash
# Discord 봇 중지
docker-compose stop discord

# Discord 봇 중지 및 삭제
docker-compose down discord
```

### 서비스 재시작

```bash
# Discord 봇 재시작
docker-compose restart discord
```

## 문제 해결

### Discord 봇이 시작되지 않음

**원인**: Discord 토큰이 설정되지 않음

**해결**:
```bash
# .env 파일 확인
cat .env | grep DISCORD_TOKEN

# 환경 변수 확인
docker-compose exec discord env | grep DISCORD_TOKEN
```

### PostgreSQL 연결 실패

**원인**: PostgreSQL 서비스가 실행되지 않음

**해결**:
```bash
# PostgreSQL 시작
docker-compose up -d postgres

# 연결 확인
docker-compose exec discord python -c "from db.postgres import PostgreSQLManager; PostgreSQLManager.initialize()"
```

### Kafka 연결 실패

**원인**: Kafka 서비스가 실행되지 않음

**해결**:
```bash
# Kafka 시작
docker-compose up -d kafka zookeeper

# 연결 확인
docker-compose exec discord python -c "from kafka import KafkaProducer; p = KafkaProducer(bootstrap_servers='kafka:29092'); print('OK')"
```

## 로그 확인

```bash
# 실시간 로그
docker-compose logs -f discord

# 최근 100줄
docker-compose logs --tail=100 discord

# 특정 키워드 검색
docker-compose logs discord | grep "error"
```

## Discord 봇 테스트

봇이 정상 작동하는지 확인:

1. Discord 서버에 봇이 온라인 상태인지 확인
2. DM 또는 채널에서 명령어 테스트:
   - `!골드`
   - `!게임목록`
   - `!게임시작 모험`

## Docker Compose 명령어

```bash
# Discord 봇만 시작
docker-compose up -d discord

# Discord 봇 로그 확인
docker-compose logs -f discord

# Discord 봇 재시작
docker-compose restart discord

# Discord 봇 중지
docker-compose stop discord

# Discord 봇 상태 확인
docker-compose ps discord
```

## 주의사항

1. **Discord 토큰 보안**: `.env` 파일을 버전 관리에 포함하지 마세요
2. **의존성**: Discord 봇은 PostgreSQL과 Kafka가 실행되어야 합니다
3. **네트워크**: 같은 Docker 네트워크(`gamebot-network`)를 사용해야 합니다

## 예시

### 전체 스택 실행

```bash
# 모든 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

### Discord 봇만 실행 (기존 인프라 사용)

```bash
# 필요한 인프라만 시작
docker-compose up -d postgres kafka zookeeper

# Discord 봇 시작
docker-compose up -d discord

# 로그 확인
docker-compose logs -f discord
```
