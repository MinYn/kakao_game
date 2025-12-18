# Gunicorn + Uvicorn 조합 설명

## 왜 둘 다 사용하나?

### 핵심 이유

1. **Gunicorn**: 프로세스 관리자 (Master Process)
   - 여러 워커 프로세스 생성/관리
   - 워커 재시작, 로드 밸런싱
   - 프로세스 모니터링

2. **Uvicorn Worker**: 실제 ASGI 서버
   - FastAPI (ASGI) 애플리케이션 실행
   - 비동기 처리
   - HTTP 프로토콜 처리

### 아키텍처

```
Gunicorn (Master Process)
    ├── Uvicorn Worker 1 → FastAPI 앱
    ├── Uvicorn Worker 2 → FastAPI 앱
    ├── Uvicorn Worker 3 → FastAPI 앱
    └── Uvicorn Worker 4 → FastAPI 앱
```

## 각각의 역할

### Gunicorn만 사용하면?

**문제**: Gunicorn은 기본적으로 WSGI 서버입니다.
- FastAPI는 ASGI 애플리케이션
- WSGI는 동기식, ASGI는 비동기식
- 직접 호환되지 않음

### Uvicorn만 사용하면?

**가능하지만 제한적**:
```bash
# 단일 프로세스로만 실행
uvicorn webhook_server:create_app --host 0.0.0.0 --port 5000

# 여러 프로세스 실행하려면?
# → 수동으로 여러 프로세스 관리 필요
# → 프로세스 모니터링 어려움
# → 워커 재시작 로직 직접 구현 필요
```

**단점**:
- 단일 프로세스만 실행 (멀티코어 활용 불가)
- 프로세스 관리 기능 부족
- 프로덕션 환경에 부적합

### Gunicorn + Uvicorn Worker 조합

**장점**:
- ✅ 여러 워커 프로세스 자동 관리
- ✅ CPU 멀티코어 활용
- ✅ 워커 자동 재시작 (메모리 누수 방지)
- ✅ 로드 밸런싱
- ✅ 프로세스 모니터링
- ✅ ASGI 애플리케이션 지원

## 실제 동작 방식

### Gunicorn 설정

```python
# gunicorn_config.py
worker_class = "uvicorn.workers.UvicornWorker"  # Uvicorn 워커 사용
workers = 4  # 4개의 워커 프로세스 생성
```

### 실행 과정

1. Gunicorn 마스터 프로세스 시작
2. 설정된 워커 수만큼 Uvicorn 워커 프로세스 생성
3. 각 워커가 FastAPI 앱 인스턴스 실행
4. 요청이 오면 Gunicorn이 워커에 분배
5. 각 워커가 Uvicorn으로 요청 처리

## 대안 비교

### 옵션 1: Gunicorn + Uvicorn Worker (현재 구성) ✅

```bash
gunicorn webhook_server:create_app -c gunicorn_config.py
```

**장점**:
- 프로덕션 환경에 최적화
- 멀티프로세싱 지원
- 자동 워커 관리

**단점**:
- 설정이 약간 복잡

### 옵션 2: Uvicorn만 사용

```bash
uvicorn webhook_server:create_app --host 0.0.0.0 --port 5000
```

**장점**:
- 간단함
- 개발 환경에 적합

**단점**:
- 단일 프로세스만 실행
- 프로덕션에 부적합

### 옵션 3: Uvicorn + 여러 프로세스 (수동)

```bash
# 여러 터미널에서 실행
uvicorn webhook_server:create_app --port 5000 &
uvicorn webhook_server:create_app --port 5001 &
uvicorn webhook_server:create_app --port 5002 &
```

**단점**:
- 수동 관리 필요
- 프로세스 모니터링 어려움
- 비추천

### 옵션 4: Hypercorn (대안)

```bash
hypercorn webhook_server:create_app --bind 0.0.0.0:5000 --workers 4
```

**장점**:
- Gunicorn 없이도 멀티프로세싱 지원
- ASGI 네이티브

**단점**:
- Gunicorn보다 덜 검증됨
- 커뮤니티가 작음

## 권장 구성

### 프로덕션 환경

```
Nginx → Gunicorn + Uvicorn Workers → FastAPI
```

**이유**:
- 안정성 검증됨
- 성능 최적화
- 운영 도구 풍부

### 개발 환경

```
Uvicorn만 사용 (단일 프로세스)
```

**이유**:
- 간단함
- 빠른 재시작
- 디버깅 용이

## 성능 비교

### 단일 Uvicorn 프로세스
- 동시 요청: ~1000 (비동기)
- CPU 활용: 1코어만 사용
- 메모리: 낮음

### Gunicorn + 4 Uvicorn Workers
- 동시 요청: ~4000 (4개 워커)
- CPU 활용: 멀티코어 활용
- 메모리: 중간 (워커당 메모리 사용)

## 결론

**Gunicorn + Uvicorn Worker 조합을 사용하는 이유:**

1. **프로세스 관리**: Gunicorn이 여러 워커를 자동 관리
2. **성능**: 멀티코어 활용으로 처리량 증가
3. **안정성**: 워커 자동 재시작으로 장애 복구
4. **ASGI 지원**: Uvicorn 워커로 FastAPI 실행 가능

**단순히 Uvicorn만 사용하면:**
- 단일 프로세스 제한
- 프로덕션 환경에 부적합
- 수동 관리 필요

**따라서 프로덕션에서는 Gunicorn + Uvicorn Worker 조합이 표준입니다.**
