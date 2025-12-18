# 게임봇 API 문서

FastAPI 기반 REST API 문서입니다.

## API 문서 자동 생성

FastAPI는 자동으로 Swagger UI와 ReDoc 문서를 제공합니다:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## 엔드포인트 목록

### 골드 관련 API (`/api/gold`)

#### 1. 골드 조회
```http
GET /api/gold/{user_id}
```

**응답 예시:**
```json
{
  "user_id": "user123",
  "gold": 1000,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### 2. 골드 추가
```http
POST /api/gold/{user_id}/add?amount=100&reason=보너스
```

**쿼리 파라미터:**
- `amount` (필수): 추가할 골드 수량 (양수)
- `reason` (선택): 추가 사유

#### 3. 골드 차감
```http
POST /api/gold/{user_id}/deduct?amount=50&reason=아이템구매
```

**쿼리 파라미터:**
- `amount` (필수): 차감할 골드 수량 (양수)
- `reason` (선택): 차감 사유

#### 4. 골드 설정 (절대값)
```http
PUT /api/gold/{user_id}
Content-Type: application/json

{
  "gold": 500
}
```

#### 5. 골드 전송
```http
POST /api/gold/transfer
Content-Type: application/json

{
  "from_user": "user1",
  "to_user": "user2",
  "amount": 100,
  "reason": "선물"
}
```

**응답 예시:**
```json
{
  "success": true,
  "from_user_balance": 900,
  "to_user_balance": 200,
  "message": "골드 전송 완료"
}
```

#### 6. 골드 이력 조회
```http
GET /api/gold/{user_id}/history?limit=10
```

**쿼리 파라미터:**
- `limit` (선택): 조회 개수 (기본값: 10, 최대: 100)

#### 7. 리더보드 조회
```http
GET /api/gold/leaderboard?limit=10
```

**응답 예시:**
```json
{
  "entries": [
    {
      "user_id": "user1",
      "gold": 10000,
      "rank": 1
    },
    {
      "user_id": "user2",
      "gold": 5000,
      "rank": 2
    }
  ],
  "total": 100
}
```

### 보스몹 입장권 API (`/api/boss-tickets`)

#### 1. 입장권 조회
```http
GET /api/boss-tickets/{user_id}
```

#### 2. 입장권 추가
```http
POST /api/boss-tickets/{user_id}/add?amount=1
```

#### 3. 입장권 사용
```http
POST /api/boss-tickets/{user_id}/use?amount=1
```

#### 4. 입장권 설정
```http
PUT /api/boss-tickets/{user_id}
Content-Type: application/json

{
  "tickets": 5
}
```

### 강화 레벨 API (`/api/enhancement`)

#### 1. 강화 레벨 조회
```http
GET /api/enhancement/{user_id}
```

#### 2. 강화 레벨 설정
```http
PUT /api/enhancement/{user_id}
Content-Type: application/json

{
  "level": 10
}
```

### 게임 통계 API (`/api/stats`)

#### 1. 통계 조회
```http
GET /api/stats/{user_id}
```

#### 2. 통계 생성/업데이트 (절대값)
```http
POST /api/stats/{user_id}
Content-Type: application/json

{
  "user_id": "user123",
  "enhancement_attempts": 10,
  "enhancement_successes": 7,
  "enhancement_failures": 3,
  "hunt_normal": 50,
  "hunt_special": 20,
  "hunt_boss": 5,
  "total_hunts": 75,
  "total_hunt_reward": 5000
}
```

#### 3. 통계 업데이트 (증가값)
```http
PATCH /api/stats/{user_id}
Content-Type: application/json

{
  "enhancement_attempts": 1,
  "enhancement_successes": 1
}
```

#### 4. 통계 설정 (절대값)
```http
PUT /api/stats/{user_id}
Content-Type: application/json

{
  "enhancement_attempts": 10,
  "enhancement_successes": 7
}
```

## 사용 예시

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:5000"

# 골드 조회
response = requests.get(f"{BASE_URL}/api/gold/user123")
gold_data = response.json()
print(f"골드: {gold_data['gold']}G")

# 골드 추가
response = requests.post(
    f"{BASE_URL}/api/gold/user123/add",
    params={"amount": 100, "reason": "보너스"}
)
print(response.json())

# 골드 전송
response = requests.post(
    f"{BASE_URL}/api/gold/transfer",
    json={
        "from_user": "user1",
        "to_user": "user2",
        "amount": 50,
        "reason": "선물"
    }
)
print(response.json())
```

### cURL

```bash
# 골드 조회
curl http://localhost:5000/api/gold/user123

# 골드 추가
curl -X POST "http://localhost:5000/api/gold/user123/add?amount=100&reason=보너스"

# 골드 전송
curl -X POST http://localhost:5000/api/gold/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_user": "user1",
    "to_user": "user2",
    "amount": 50,
    "reason": "선물"
  }'
```

## Kafka 이벤트

모든 골드 트랜잭션과 통계 업데이트는 Kafka 이벤트로 발행됩니다:

- `gold-events`: 골드 추가/차감/전송 이벤트
- `stats-events`: 통계 업데이트 이벤트

## 에러 처리

API는 표준 HTTP 상태 코드를 사용합니다:

- `200`: 성공
- `400`: 잘못된 요청 (예: 골드 부족)
- `404`: 리소스를 찾을 수 없음
- `500`: 서버 오류

에러 응답 형식:
```json
{
  "detail": "골드가 부족합니다"
}
```
