# Nginx 접근 문제 해결 가이드

## 문제 진단

### 1. 컨테이너 상태 확인

```bash
docker-compose ps
```

**정상 상태:**
- `nginx`: Up (healthy)
- `gamebot`: Up (healthy)

### 2. Nginx 로그 확인

```bash
# Nginx 에러 로그
docker-compose logs nginx

# 실시간 로그
docker-compose logs -f nginx
```

### 3. 포트 확인

```bash
# 포트 사용 확인
lsof -i :8080
# 또는
netstat -an | grep 8080

# 다른 포트로 테스트
EXTERNAL_PORT=3000 docker-compose up -d
```

### 4. 직접 접근 테스트

```bash
# 헬스 체크
curl http://localhost:8080/health

# API 테스트
curl http://localhost:8080/api/gold/test_user

# API 문서
curl http://localhost:8080/docs
```

## 일반적인 문제와 해결

### 문제 1: Nginx가 unhealthy 상태

**원인**: Healthcheck 실패

**해결**:
```bash
# Nginx 재시작
docker-compose restart nginx

# Healthcheck 비활성화 (임시)
# docker-compose.yml에서 healthcheck 주석 처리
```

### 문제 2: Connection refused

**원인**: Gamebot 서비스가 준비되지 않음

**해결**:
```bash
# Gamebot 로그 확인
docker-compose logs gamebot

# Gamebot 재시작
docker-compose restart gamebot

# 모든 서비스 재시작
docker-compose restart
```

### 문제 3: 502 Bad Gateway

**원인**: Nginx가 Gamebot에 연결할 수 없음

**해결**:
```bash
# 네트워크 확인
docker network inspect kakao_game_gamebot-network

# Gamebot 직접 연결 테스트
docker-compose exec nginx wget -O- http://gamebot:5000/health
```

### 문제 4: 포트가 이미 사용 중

**원인**: 다른 프로세스가 포트 사용

**해결**:
```bash
# 포트 사용 프로세스 확인
lsof -i :8080

# 다른 포트 사용
EXTERNAL_PORT=3000 docker-compose up -d
```

### 문제 5: Nginx 설정 오류

**원인**: nginx.conf 문법 오류

**해결**:
```bash
# 설정 검증
docker-compose exec nginx nginx -t

# 설정 파일 확인
cat nginx/nginx.conf
```

## 빠른 해결 방법

### 전체 재시작

```bash
# 모든 서비스 중지
docker-compose down

# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### Nginx만 재시작

```bash
docker-compose restart nginx
```

### 설정 파일 다시 로드

```bash
# Nginx 설정 다시 로드
docker-compose exec nginx nginx -s reload
```

## 진단 스크립트 사용

```bash
# 진단 스크립트 실행
./scripts/check_nginx.sh
```

## 접근 확인 체크리스트

- [ ] Nginx 컨테이너가 실행 중인가?
- [ ] Gamebot 컨테이너가 healthy 상태인가?
- [ ] 포트 8080이 열려있는가?
- [ ] 네트워크가 올바르게 설정되었는가?
- [ ] Nginx 설정 파일이 올바른가?
- [ ] Gamebot이 포트 5000에서 응답하는가?

## 성공 확인

다음 명령어들이 모두 성공하면 정상 작동:

```bash
# 1. 헬스 체크
curl http://localhost:8080/health
# 응답: {"status":"ok"}

# 2. API 테스트
curl http://localhost:8080/api/gold/test_user
# 응답: 골드 데이터 JSON

# 3. API 문서 접근
curl http://localhost:8080/docs
# 응답: HTML 페이지
```

## 추가 도움말

문제가 계속되면:
1. `docker-compose logs` 전체 확인
2. `docker-compose ps` 상태 확인
3. 네트워크 및 포트 확인
4. 설정 파일 검증
