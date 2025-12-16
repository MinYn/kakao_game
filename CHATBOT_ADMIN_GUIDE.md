# 카카오 챗봇 관리자센터 연동 가이드

이 가이드는 카카오 챗봇 관리자센터를 사용하여 완전 무료로 챗봇을 개발하는 방법을 설명합니다.

**참고 문서**: [카카오 챗봇 관리자센터 가이드](https://kakaobusiness.gitbook.io/main/tool/chatbot)

---

## 개요

카카오 챗봇 관리자센터는 카카오톡 채널을 통해 사용자와 상호작용하는 챗봇을 생성, 관리, 배포할 수 있는 플랫폼입니다. **스킬 서버**를 통해 외부 서버와 연동하여 복잡한 로직을 구현할 수 있습니다.

### 주요 개념

- **스킬(Skill)**: 사용자의 입력에 대한 챗봇의 응답을 정의하는 단위
- **블록(Block)**: 여러 개의 스킬을 묶어 하나의 흐름을 구성하는 단위
- **시나리오(Scenario)**: 블록들을 조합하여 전체적인 대화 흐름을 정의
- **스킬 서버**: 외부 서버에서 챗봇 로직을 처리하는 서버

---

## 1단계: 챗봇 관리자센터 접속 및 챗봇 생성

### 1.1 챗봇 관리자센터 접속

1. **챗봇 관리자센터 접속**
   - https://i.kakao.com/ 접속
   - 또는 카카오 비즈니스 → 서비스/도구 → 챗봇 관리자센터

2. **카카오 계정으로 로그인**
   - 카카오 계정으로 로그인
   - 처음 사용하는 경우 약관 동의 필요

### 1.2 챗봇 생성

1. **새 챗봇 만들기**
   - 챗봇 관리자센터 대시보드에서 **"새 챗봇 만들기"** 클릭
   - 챗봇 이름 입력 (예: "게임봇")
   - 카카오톡 채널 선택 (이미 생성된 채널이 있어야 함)

2. **챗봇 기본 설정**
   - 챗봇 프로필 이미지 설정
   - 챗봇 소개글 입력
   - 저장

---

## 2단계: 스킬 서버 개발

### 2.1 스킬 서버 실행

**로컬 개발 환경:**

```bash
# 웹훅 서버 실행 (스킬 서버)
python main.py kakao --webhook
```

서버가 실행되면 다음 URL이 표시됩니다:
```
웹훅 URL: http://0.0.0.0:5000/webhook
```

### 2.2 ngrok으로 로컬 서버 노출 (무료)

```bash
# 다른 터미널에서 ngrok 실행
ngrok http 5000
```

ngrok이 제공하는 HTTPS URL 예시:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:5000
```

**스킬 서버 URL**: `https://abc123.ngrok.io/webhook`

---

## 3단계: 챗봇 관리자센터에서 스킬 등록

### 3.1 스킬 만들기

1. **스킬 메뉴 접속**
   - 챗봇 관리자센터 → **"스킬"** 메뉴 클릭
   - **"스킬 만들기"** 버튼 클릭

2. **스킬 정보 입력**
   - **스킬 이름**: 원하는 이름 입력 (예: "게임봇 스킬")
   - **스킬 설명**: 스킬에 대한 설명 입력

3. **스킬 서버 URL 설정**
   - **스킬 서버 URL**: `https://abc123.ngrok.io/webhook` 입력
   - 또는 배포된 서버 URL: `https://yourdomain.com/webhook`
   - **저장**

### 3.2 스킬 테스트

1. **스킬 테스트**
   - 스킬 상세 페이지에서 **"테스트"** 버튼 클릭
   - 테스트 메시지 입력 (예: "안녕")
   - 응답 확인

---

## 4단계: 블록에 스킬 적용

### 4.1 블록 생성

1. **시나리오 편집**
   - 챗봇 관리자센터 → **"시나리오"** 메뉴
   - **"새 블록 만들기"** 클릭

2. **블록 설정**
   - 블록 이름 입력 (예: "게임 블록")
   - 발화 패턴 설정 (예: "게임", "놀자", "게임 시작")

### 4.2 스킬 적용

1. **스킬 선택**
   - 블록 편집 화면에서 **"스킬"** 선택
   - 앞서 만든 스킬 선택 (예: "게임봇 스킬")

2. **응답 설정**
   - 스킬 서버에서 반환하는 응답이 자동으로 사용됨
   - 추가 응답 설정 가능

3. **저장 및 배포**
   - 블록 저장
   - **"배포"** 버튼 클릭하여 챗봇 배포

---

## 5단계: 카카오톡 채널 연결

### 5.1 채널 연결 확인

1. **채널 설정**
   - 챗봇 관리자센터 → **"봇 설정"** → **"채널 연결"**
   - 카카오톡 채널이 연결되어 있는지 확인

2. **채널 활성화**
   - 카카오 비즈니스에서 채널이 활성화되어 있어야 함
   - 챗봇이 활성화되어 있어야 함

### 5.2 테스트

1. **카카오톡에서 테스트**
   - 카카오톡 앱에서 채널 검색
   - 채널 추가 후 메시지 전송
   - 봇이 응답하는지 확인

---

## 스킬 서버 요청/응답 형식

### 요청 형식

카카오 챗봇 관리자센터가 스킬 서버로 보내는 요청 형식:

```json
{
  "userRequest": {
    "user": {
      "id": "user_id_12345"
    },
    "utterance": "사용자가 입력한 메시지"
  },
  "bot": {
    "id": "bot_id",
    "name": "봇 이름"
  },
  "action": {
    "id": "action_id",
    "name": "액션 이름",
    "params": {}
  }
}
```

### 응답 형식

스킬 서버가 반환해야 하는 응답 형식:

```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "simpleText": {
          "text": "응답 메시지"
        }
      }
    ]
  }
}
```

**다양한 응답 타입:**

1. **간단한 텍스트**:
```json
{
  "simpleText": {
    "text": "안녕하세요!"
  }
}
```

2. **이미지 포함**:
```json
{
  "simpleImage": {
    "imageUrl": "https://example.com/image.jpg",
    "altText": "이미지 설명"
  }
}
```

3. **카드형 응답**:
```json
{
  "basicCard": {
    "title": "제목",
    "description": "설명",
    "thumbnail": {
      "imageUrl": "https://example.com/image.jpg"
    },
    "buttons": [
      {
        "action": "message",
        "label": "버튼 텍스트",
        "messageText": "버튼 클릭 시 전송될 메시지"
      }
    ]
  }
}
```

자세한 응답 타입은 [응답 타입별 JSON 포맷](https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide/answer_json_format) 참조

---

## 코드 구조

현재 프로젝트의 스킬 서버 코드는 `webhook_server.py`에 구현되어 있습니다:

```python
# 요청 파싱
user_id, message = self._parse_user_request(data)

# 게임 엔진으로 메시지 처리
response_text = self.engine.process_message(user_id, message)

# 응답 생성
response = self._create_response(response_text)
```

---

## 배포 방법

### 로컬 개발 (ngrok 사용)

```bash
# 터미널 1: 스킬 서버 실행
python main.py kakao --webhook

# 터미널 2: ngrok 실행
ngrok http 5000
```

ngrok URL을 스킬 서버 URL로 등록

### 서버 배포 (무료 호스팅)

**Railway 사용:**
```bash
railway login
railway init
railway up
```

**Render 사용:**
1. https://render.com/ 접속
2. New Web Service 선택
3. GitHub 저장소 연결
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python main.py kakao`
6. Deploy 후 제공되는 URL을 스킬 서버 URL로 등록

---

## 문제 해결

### 스킬 서버가 응답하지 않는 경우

1. **서버 실행 확인**
   ```bash
   curl http://localhost:5000/health
   ```

2. **ngrok 연결 확인**
   - ngrok 대시보드에서 요청 로그 확인
   - https://dashboard.ngrok.com/ 접속

3. **스킬 서버 URL 확인**
   - 챗봇 관리자센터에서 스킬 서버 URL이 정확한지 확인
   - HTTPS 필수 (HTTP는 사용 불가)

### 응답 형식 오류

- 스킬 서버가 올바른 JSON 형식으로 응답하는지 확인
- `webhook_server.py`의 `_create_response` 메서드 확인

### 메시지가 전달되지 않는 경우

1. **블록 설정 확인**
   - 발화 패턴이 올바르게 설정되었는지 확인
   - 스킬이 블록에 적용되었는지 확인

2. **배포 확인**
   - 챗봇이 배포되었는지 확인
   - 배포 후 일정 시간(몇 분) 대기

3. **채널 연결 확인**
   - 카카오톡 채널이 정상적으로 연결되어 있는지 확인

---

## 참고 자료

- **챗봇 관리자센터 가이드**: https://kakaobusiness.gitbook.io/main/tool/chatbot
- **스킬 개발 가이드**: https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide
- **응답 타입별 JSON 포맷**: https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide/answer_json_format
- **카카오 비즈니스**: https://business.kakao.com/
- **챗봇 관리자센터**: https://i.kakao.com/

---

## 완료 확인

다음 항목이 모두 완료되면 설정이 완료된 것입니다:

- [ ] 챗봇 관리자센터에서 챗봇 생성 완료
- [ ] 스킬 서버 실행 및 ngrok 설정 완료
- [ ] 챗봇 관리자센터에서 스킬 등록 완료
- [ ] 블록에 스킬 적용 완료
- [ ] 챗봇 배포 완료
- [ ] 카카오톡에서 메시지 전송 시 봇이 응답함

설정이 완료되면 이제 완전 무료로 카카오톡 챗봇을 사용할 수 있습니다! 🎉

