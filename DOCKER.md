# Docker 사용 가이드

## 개요

FastAPI 기반 웹훅 서버를 Docker 컨테이너에서 실행하여 카카오 챗봇 관리자센터와 연동합니다.

## 사전 요구사항

- Docker Desktop 또는 Docker Engine 설치
- Docker Compose 설치 (일반적으로 Docker Desktop에 포함됨)

## 빠른 시작

### 1. Docker 설치 확인

```bash
docker --version
docker-compose --version
```

### 2. 환경 변수 설정

`.env` 파일에 필요한 환경 변수를 설정합니다:

```env
PLATFORM=kakao
INITIAL_POINTS=100
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
POINTS_DATA_FILE=/app/data/points_data.db
```

### 3. Docker 이미지 빌드

```bash
docker-compose build
```

### 4. 컨테이너 실행

```bash
# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f gamebot
```

### 5. 컨테이너 중지

```bash
docker-compose down
```

## 주요 명령어

### 컨테이너 관리

```bash
# 컨테이너 시작
docker-compose start

# 컨테이너 중지
docker-compose stop

# 컨테이너 재시작
docker-compose restart

# 컨테이너 삭제 (데이터는 유지)
docker-compose down

# 컨테이너 및 볼륨 삭제 (데이터도 삭제)
docker-compose down -v
```

### 로그 확인

```bash
# 전체 로그 확인
docker-compose logs

# 실시간 로그 확인
docker-compose logs -f

# 최근 100줄만 확인
docker-compose logs --tail=100
```

### 컨테이너 내부 접속

```bash
# 컨테이너 내부 쉘 접속
docker-compose exec gamebot /bin/bash

# Python 실행
docker-compose exec gamebot python main.py kakao
```

## 볼륨 관리

### 명명된 볼륨 (권장)

`docker-compose.yml`에서 다음 명명된 볼륨이 사용됩니다:

- `gamebot_data`: 데이터베이스 및 게임 데이터 저장 (`/app/data`)
- `gamebot_logs`: 로그 파일 저장 (`/app/logs`)

**볼륨 확인:**
```bash
# 볼륨 목록 확인
docker volume ls

# 볼륨 상세 정보 확인
docker volume inspect kakao_game_gamebot_data
```

**볼륨 백업:**
```bash
# 볼륨 데이터 백업
docker run --rm -v kakao_game_gamebot_data:/data -v $(pwd):/backup alpine tar czf /backup/gamebot_data_backup.tar.gz -C /data .
```

**볼륨 복원:**
```bash
# 볼륨 데이터 복원
docker run --rm -v kakao_game_gamebot_data:/data -v $(pwd):/backup alpine tar xzf /backup/gamebot_data_backup.tar.gz -C /data
```

### 바인드 마운트 (로컬 개발용)

로컬 개발 시 호스트 디렉토리와 동기화하려면 `docker-compose.yml`에서 다음 줄의 주석을 해제하세요:

```yaml
volumes:
  # - ./data:/app/data  # 주석 해제
```

이렇게 하면 호스트의 `./data` 디렉토리가 컨테이너의 `/app/data`와 동기화됩니다.

## 문제 해결

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker-compose logs gamebot

# 이미지 재빌드
docker-compose build --no-cache

# 컨테이너 재시작
docker-compose restart
```

### 포트 충돌

`docker-compose.yml`에서 포트 설정을 변경할 수 있습니다:

```yaml
ports:
  - "5001:5000"  # 호스트:컨테이너 (호스트 포트 변경)
```

### 데이터베이스 파일 권한 문제

```bash
# 볼륨 내부 파일 확인
docker-compose exec gamebot ls -la /app/data

# 권한 수정 (필요한 경우)
docker-compose exec gamebot chmod 666 /app/data/points_data.db
```

### 웹훅 서버 상태 확인

```bash
# 웹훅 서버 헬스 체크
curl http://localhost:5000/health

# 컨테이너 재시작
docker-compose restart gamebot
```

## 프로덕션 배포

프로덕션 환경에서는 다음을 고려하세요:

1. **환경 변수 관리**: Docker secrets 또는 환경 변수 파일 사용
2. **로그 관리**: 로그 로테이션 설정
3. **모니터링**: 헬스 체크 및 모니터링 도구 설정
4. **백업**: 볼륨 데이터 정기 백업
5. **보안**: HTTPS 사용, 방화벽 설정

## 추가 리소스

- Docker 공식 문서: https://docs.docker.com/
- Docker Compose 문서: https://docs.docker.com/compose/
- FastAPI 문서: https://fastapi.tiangolo.com/
- 카카오 챗봇 관리자센터: https://i.kakao.com/
- 챗봇 관리자센터 가이드: `CHATBOT_ADMIN_GUIDE.md` 참조

