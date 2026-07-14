# 파라미터 설정 가이드

카카오 챗봇 관리자센터에서 파라미터를 설정하는 방법과 스킬 서버에서 받는 방법을 설명합니다.

> 현재 제공되는 게임은 **우주 탐험 로그(우주선 강화 + 임무 + 도감/득템)** 하나입니다. 숫자맞추기/가위바위보 예시는 과거 버전용이므로 무시하세요.

---

## 파라미터란?

파라미터는 스킬 서버로 전달할 추가 정보를 정의하는 것입니다. 엔티티에서 추출한 값이나 사용자 발화를 파라미터로 전달할 수 있습니다.

---

## 게임봇의 경우

### 권장: 파라미터 설정 안 함 ⭐

**이유**:
- 설정이 간단함
- 스킬 서버에서 `userRequest.utterance`를 직접 파싱하여 처리 가능
- 모든 명령어를 하나의 엔드포인트에서 처리

**스킬 서버에서 처리**:
```python
# webhook_server.py
data = await request.json()
utterance = data.get('userRequest', {}).get('utterance', '')
# utterance를 직접 파싱: "골드", "게임시작 숫자맞추기" 등
response = self.engine.process_message(user_id, utterance)
```

---

## 파라미터 설정 방법

### 1. 일반 파라미터 추가

**블록 편집 화면에서**:

1. **"파라미터 설정"** 섹션 확인
2. **"일반 파라미터"** 박스에서 **"+"** 버튼 클릭
3. 파라미터 정보 입력:
   - **파라미터 이름**: `message` (또는 원하는 이름)
   - **파라미터 타입**: `String` 선택
   - **기본값**: `@{userRequest.utterance}` 입력
     - 이렇게 하면 사용자 발화 전체가 파라미터로 전달됨
4. **저장** 또는 **확인**

**파라미터 타입 옵션**:
- `String`: 문자열
- `Number`: 숫자
- `Boolean`: 불린 (true/false)
- `Date`: 날짜
- `Time`: 시간

### 2. 필수 파라미터 추가

**필수 파라미터는 값이 없으면 블록이 실행되지 않습니다.**

1. **"필수 파라미터"** 박스에서 **"+"** 버튼 클릭
2. 파라미터 정보 입력:
   - **파라미터 이름**: `message`
   - **파라미터 타입**: `String`
   - **필수 여부**: 체크 ✅
3. **저장**

**주의**: 필수 파라미터는 값이 없으면 블록이 실행되지 않으므로, 게임봇의 경우 사용하지 않는 것을 권장합니다.

---

## 파라미터 기본값 설정

### 사용자 발화 전체 전달

**기본값**: `@{userRequest.utterance}`

이렇게 설정하면 사용자가 입력한 메시지 전체가 파라미터로 전달됩니다.

**예시**:
- 사용자 입력: `골드`
- 파라미터 `message`: `"골드"`

### 엔티티 값 전달

**기본값**: `@{엔티티이름}`

엔티티를 사용하는 경우, 엔티티에서 추출한 값을 파라미터로 전달할 수 있습니다.

**예시**:
- 발화 패턴: `게임시작 {게임이름}`
- 엔티티: `게임이름` (값: "숫자맞추기")
- 파라미터 기본값: `@{게임이름}`
- 파라미터 `gameName`: `"숫자맞추기"`

### 고정값 전달

**기본값**: `"고정값"`

고정된 값을 파라미터로 전달할 수 있습니다.

**예시**:
- 파라미터 기본값: `"gamebot"`
- 파라미터 `botType`: `"gamebot"`

---

## 스킬 서버에서 파라미터 받기

### 요청 형식

**파라미터를 사용하는 경우**:
```json
{
  "userRequest": {
    "user": {
      "id": "user123"
    },
    "utterance": "골드"
  },
  "action": {
    "id": "action_id",
    "name": "액션 이름",
    "params": {
      "message": "골드"
    }
  }
}
```

### Python 코드에서 파라미터 받기

**webhook_server.py**:
```python
async def webhook(request: Request):
    data = await request.json()
    
    # 방법 1: 파라미터에서 받기
    action = data.get('action', {})
    params = action.get('params', {})
    message = params.get('message', '')
    
    # 방법 2: utterance에서 직접 받기 (권장)
    utterance = data.get('userRequest', {}).get('utterance', '')
    
    # 둘 다 사용 가능하지만, utterance를 직접 사용하는 것이 간단함
    user_id = data.get('userRequest', {}).get('user', {}).get('id', '')
    response_text = self.engine.process_message(user_id, utterance)
    
    return JSONResponse(content=self._create_response(response_text))
```

---

## 파라미터 사용 예시

### 예시 1: 사용자 발화 전체 전달

**파라미터 설정**:
- 이름: `message`
- 타입: `String`
- 기본값: `@{userRequest.utterance}`

**요청**:
```json
{
  "action": {
    "params": {
      "message": "골드"
    }
  }
}
```

**스킬 서버**:
```python
message = params.get('message', '')  # "골드"
```

### 예시 2: 엔티티 값 전달

**발화 패턴**: `게임시작 {게임이름}`

**파라미터 설정**:
- 이름: `gameName`
- 타입: `String`
- 기본값: `@{게임이름}`

**요청**:
```json
{
  "userRequest": {
    "utterance": "게임시작 숫자맞추기"
  },
  "action": {
    "params": {
      "gameName": "숫자맞추기"
    }
  }
}
```

**스킬 서버**:
```python
game_name = params.get('gameName', '')  # "숫자맞추기"
```

### 예시 3: 여러 파라미터 사용

**발화 패턴**: `골드주기 {사용자} {금액}`

**파라미터 설정**:
1. `toUser` (기본값: `@{사용자}`)
2. `amount` (기본값: `@{금액}`)

**요청**:
```json
{
  "action": {
    "params": {
      "toUser": "alice",
      "amount": "50"
    }
  }
}
```

**스킬 서버**:
```python
to_user = params.get('toUser', '')  # "alice"
amount = int(params.get('amount', '0'))  # 50
```

---

## 게임봇 권장 설정

### 권장: 파라미터 설정 안 함

**이유**:
1. **간단함**: 파라미터 설정 불필요
2. **유연함**: 스킬 서버에서 모든 파싱 처리 가능
3. **유지보수**: 새로운 명령어 추가 시 시나리오 수정 불필요

**현재 구현**:
- 파라미터 없이 `userRequest.utterance`를 직접 파싱
- 모든 명령어를 `game_engine.py`에서 처리

### 파라미터를 사용하는 경우

**사용 시나리오**:
- 엔티티를 사용하여 발화 패턴을 더 명확하게 만들고 싶을 때
- 파라미터로 명확한 값 전달이 필요할 때

**주의사항**:
- 파라미터를 사용해도 `userRequest.utterance`는 항상 전달됨
- 파라미터 없이도 동작하므로 필수는 아님

---

## 파라미터 vs 엔티티

### 엔티티
- 발화 패턴에서 값을 추출하는 것
- 예: `게임시작 {게임이름}` → `게임이름` 엔티티

### 파라미터
- 엔티티에서 추출한 값을 스킬 서버로 전달하는 것
- 예: `@{게임이름}` → `gameName` 파라미터

**관계**:
- 엔티티를 사용하면 파라미터로 전달 가능
- 하지만 엔티티 없이도 파라미터 설정 가능 (기본값 사용)

---

## 문제 해결

### 파라미터가 전달되지 않는 경우

1. **파라미터 기본값 확인**
   - `@{userRequest.utterance}` 또는 `@{엔티티이름}` 형식 확인
2. **스킬 서버 로그 확인**
   - 요청 JSON에서 `action.params` 확인
3. **필수 파라미터 확인**
   - 필수 파라미터가 값이 없으면 블록이 실행되지 않음

### 파라미터 값이 비어있는 경우

1. **기본값 설정 확인**
   - 기본값이 올바르게 설정되었는지 확인
2. **엔티티 매칭 확인**
   - 엔티티가 제대로 추출되었는지 확인
3. **스킬 서버에서 기본값 처리**
   ```python
   message = params.get('message', '') or utterance
   ```

---

## 요약

### 게임봇 권장 설정

✅ **파라미터 설정 안 함**
- "일반 파라미터가 없습니다." 상태 유지
- "필수 파라미터가 없습니다." 상태 유지
- 스킬 서버에서 `userRequest.utterance` 직접 파싱

### 파라미터를 사용하는 경우

1. **일반 파라미터 추가**
   - 이름: `message`
   - 기본값: `@{userRequest.utterance}`
2. **스킬 서버에서 받기**
   ```python
   params = data.get('action', {}).get('params', {})
   message = params.get('message', '')
   ```

**결론**: 게임봇의 경우 파라미터 없이 사용하는 것을 권장합니다! 🎉

