# 서버 설정 가이드

## 아키텍처

```
외부 요청 → Nginx (포트 3000, 기본값) → Gunicorn + Uvicorn Workers → FastAPI 앱
```

## 포트 설정

### 환경변수로 포트 설정

`.env` 파일에 다음 설정 추가:

```env
# 외부 포트 (Nginx가 노출하는 포트, 기본값: 3000)
EXTERNAL_PORT=3000

# 내부 포트 (FastAPI 앱이 실행되는 포트)
SERVER_PORT=5000

# Gunicorn 워커 수 (CPU 코어 수 * 2 + 1 권장)
GUNICORN_WORKERS=4

# Gunicorn 사용 여부 (프로덕션: true, 개발: false)
USE_GUNICORN=true

# Nginx 사용 여부
USE_NGINX=true
```

### 포트 변경 예시

```bash
# 포트 3000으로 변경
EXTERNAL_PORT=3000

# 포트 80 (HTTP)으로 변경
EXTERNAL_PORT=80

# 포트 443 (HTTPS) 사용 시 Nginx SSL 설정 필요
EXTERNAL_PORT=443
```

## 서버 구성 요소

### 1. Nginx (리버스 프록시)

- **역할**: 외부 요청을 받아 FastAPI 앱으로 전달
- **포트**: 환경변수 `EXTERNAL_PORT`로 설정 (기본값: 3000, Jenkins가 8080 사용 중)
- **설정 파일**: `nginx/nginx.conf`

**주요 기능:**
- 리버스 프록시
- 로드 밸런싱 (여러 워커 지원)
- 정적 파일 서빙 (필요시)
- SSL/TLS 종료 (HTTPS 설정 시)

### 2. Gunicorn (WSGI 서버)

- **역할**: Python 애플리케이션 서버
- **워커**: Uvicorn 워커 사용 (ASGI 지원)
- **설정 파일**: `gunicorn_config.py`

**주요 설정:**
- 워커 수: CPU 코어 수 * 2 + 1 (기본값)
- 타임아웃: 60초
- 최대 요청: 1000개 후 워커 재시작

### 3. Uvicorn Workers

- **역할**: ASGI 워커 프로세스
- **특징**: 비동기 처리 지원

## 실행 방법

### Docker Compose로 실행 (권장)

```bash
# 전체 스택 시작 (Nginx + Gunicorn + FastAPI)
docker-compose up -d

# 로그 확인
docker-compose logs -f nginx
docker-compose logs -f gamebot

# 특정 포트로 실행
EXTERNAL_PORT=3000 docker-compose up -d
```

### 개발 모드 (Gunicorn 없이)

```env
USE_GUNICORN=false
USE_NGINX=false
```

```bash
# 직접 실행
python main.py kakao

# 또는 Uvicorn 직접 실행
uvicorn webhook_server:create_app --host 0.0.0.0 --port 5000
```

## 성능 튜닝

### Gunicorn 워커 수 조정

```env
# CPU 코어 수에 맞게 조정
GUNICORN_WORKERS=8  # 4코어 CPU의 경우
```

**권장 공식:**
- CPU 바운드: `(2 × CPU 코어 수) + 1`
- I/O 바운드: `(4 × CPU 코어 수)`

### Nginx 설정 조정

`nginx/nginx.conf`에서 다음 설정 조정:

```nginx
# 클라이언트 최대 요청 크기
client_max_body_size 10M;

# 타임아웃 설정
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

## HTTPS 설정 (선택사항)

### 1. SSL 인증서 준비

Let's Encrypt 또는 기타 인증서 사용:

```bash
# 인증서 파일 위치
/etc/ssl/certs/cert.pem
/etc/ssl/private/key.pem
```

### 2. Nginx 설정 수정

`nginx/nginx.conf`에 SSL 설정 추가:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    # SSL 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... 나머지 설정
}

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Docker Compose 업데이트

```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - ./ssl:/etc/ssl:ro  # SSL 인증서 마운트
  ports:
    - "443:443"
    - "80:80"
```

## 모니터링

### 헬스 체크

```bash
# Nginx를 통한 헬스 체크
curl http://localhost:3000/health

# 직접 앱 헬스 체크
curl http://localhost:5000/health
```

### 로그 확인

```bash
# Nginx 액세스 로그
docker-compose exec nginx tail -f /var/log/nginx/access.log

# Nginx 에러 로그
docker-compose exec nginx tail -f /var/log/nginx/error.log

# 애플리케이션 로그
docker-compose logs -f gamebot
```

## 문제 해결

### 포트가 이미 사용 중

```bash
# 포트 사용 확인
lsof -i :8080

# 다른 포트 사용
EXTERNAL_PORT=3000 docker-compose up -d
```

### Nginx 연결 실패

```bash
# Nginx 설정 검증
docker-compose exec nginx nginx -t

# Nginx 재시작
docker-compose restart nginx
```

### Gunicorn 워커가 시작되지 않음

```bash
# 로그 확인
docker-compose logs gamebot

# 워커 수 줄이기
GUNICORN_WORKERS=2 docker-compose up -d
```

## 성능 벤치마크

### 테스트 도구

```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:8080/health

# wrk
wrk -t4 -c100 -d30s http://localhost:8080/health
```

## 참고사항

- **프로덕션**: Nginx + Gunicorn 조합 권장
- **개발**: Uvicorn 직접 실행 가능
- **포트 변경**: 환경변수 `EXTERNAL_PORT`로 간단히 변경 가능
- **워커 수**: 트래픽에 따라 조정 필요
