# Quick Replies (빠른 응답) 버튼 가이드

카카오톡에서 봇 멘션(`@봇이름`) 시 표시되는 커맨드 버튼 설정 가이드입니다.

---

## 개요

**Quick Replies**는 카카오톡 챗봇에서 사용자가 봇을 멘션(`@봇이름`)하거나 특정 상황에서 자동으로 표시되는 **빠른 응답 버튼**입니다.

이미지에서 보이는 것처럼:
- 하단에 "강화", "배틀", "랭킹", "판매", "묵념", "프로필" 등의 버튼이 표시됨
- 사용자가 버튼을 클릭하면 해당 명령어가 자동으로 전송됨

---

## 구현 방식

### 1. 스킬 서버 응답에 Quick Replies 추가

**응답 형식**:
```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "simpleText": {
          "text": "응답 메시지",
          "extra": {}
        }
      }
    ],
    "quickReplies": [
      {
        "action": "message",
        "label": "💰 골드",
        "messageText": "골드"
      },
      {
        "action": "message",
        "label": "🎮 게임시작",
        "messageText": "게임시작 모험"
      }
    ]
  }
}
```

**필드 설명**:
- `action`: 버튼 동작 타입 (`"message"` = 메시지 전송)
- `label`: 버튼에 표시될 텍스트 (이모지 포함 가능)
- `messageText`: 버튼 클릭 시 실제로 전송될 메시지

---

## 게임봇 Quick Replies 설정

### 기본 Quick Replies (일반 상황)

**표시되는 버튼**:
- 💰 골드 → `골드` 명령 전송
- 🎮 게임시작 → `게임시작 모험` 명령 전송
- 🏆 랭킹 → `리더보드` 명령 전송
- 📋 게임목록 → `게임목록` 명령 전송
- ❓ 도움말 → `도움말` 명령 전송

**사용 시나리오**:
- 게임이 시작되지 않은 상태
- 일반 명령어 입력 시
- 봇 멘션(`@게임봇`) 시

### 모험 게임 Quick Replies (게임 중)

**표시되는 버튼**:
- 🔨 강화 → `강화` 명령 전송
- 🗡️ 사냥 → `사냥` 명령 전송
- 💰 판매 → `판매` 명령 전송
- 📊 상태 → `상태` 명령 전송
- 🏆 랭킹 → `리더보드` 명령 전송
- ❌ 종료 → `게임종료` 명령 전송

**사용 시나리오**:
- 모험 게임이 활성화된 상태
- 게임 중 명령어 입력 시

---

## 코드 구현

### `webhook_server.py` 구현

**기본 Quick Replies 생성**:
```python
def _get_default_quick_replies(self) -> list:
    """기본 Quick Replies 버튼 목록 생성"""
    return [
        {
            'action': 'message',
            'label': '💰 골드',
            'messageText': '골드'
        },
        {
            'action': 'message',
            'label': '🎮 게임시작',
            'messageText': '게임시작 모험'
        },
        # ... 더 많은 버튼
    ]
```

**모험 게임 Quick Replies 생성**:
```python
def _get_adventure_quick_replies(self) -> list:
    """모험 게임 중 Quick Replies 버튼 목록 생성"""
    return [
        {
            'action': 'message',
            'label': '🔨 강화',
            'messageText': '강화'
        },
        {
            'action': 'message',
            'label': '🗡️ 사냥',
            'messageText': '사냥'
        },
        # ... 더 많은 버튼
    ]
```

**응답 생성 시 Quick Replies 추가**:
```python
def _create_response(
    self,
    text: str,
    quick_replies: Optional[list] = None
) -> Dict[str, Any]:
    """응답 생성 (Quick Replies 포함)"""
    if quick_replies is None:
        quick_replies = self._get_default_quick_replies()
    
    return {
        'version': '2.0',
        'template': {
            'outputs': [
                {
                    'simpleText': {
                        'text': text,
                        'extra': {}
                    }
                }
            ],
            'quickReplies': quick_replies
        }
    }
```

**게임 상태에 따라 Quick Replies 선택**:
```python
# 메시지 처리
response_text = self.engine.process_message(user_id, message)

# Quick Replies 버튼 결정
quick_replies = None
if self.engine.has_active_game(user_id):
    game = self.engine.active_games.get(user_id)
    if game and game.__class__.__name__ == 'AdventureGame':
        quick_replies = self._get_adventure_quick_replies()

# 응답 생성
response = self._create_response(response_text, quick_replies)
```

---

## 카카오톡에서 확인 방법

### 1. 봇 멘션 시 버튼 표시

1. **카카오톡에서 챗봇과 대화 시작**
2. **`@봇이름` 입력**
   - 예: `@게임봇`
3. **하단에 버튼 표시 확인**
   - 💰 골드, 🎮 게임시작, 🏆 랭킹 등 버튼이 표시됨
4. **버튼 클릭**
   - 버튼을 클릭하면 해당 명령어가 자동으로 전송됨

### 2. 일반 메시지 입력 시 버튼 표시

1. **일반 메시지 입력**
   - 예: `골드`
2. **응답과 함께 버튼 표시 확인**
   - 응답 메시지 아래에 Quick Replies 버튼이 표시됨

### 3. 게임 중 버튼 표시

1. **모험 게임 시작**
   - `게임시작 모험` 또는 `@게임봇 게임시작 모험`
2. **게임 중 응답 확인**
   - 🔨 강화, 🗡️ 사냥, 💰 판매 등 게임 관련 버튼이 표시됨

---

## Quick Replies 제한 사항

### 버튼 개수 제한

- **최대 10개**: Quick Replies 버튼은 최대 10개까지 표시 가능
- **권장 5-6개**: 너무 많으면 사용자가 혼란스러울 수 있음

### 버튼 텍스트 제한

- **라벨 길이**: 버튼 라벨은 짧고 명확하게 (예: "💰 골드")
- **이모지 사용**: 이모지를 사용하면 시각적으로 구분하기 쉬움

### 동작 제한

- **메시지 전송만 가능**: `action: "message"`만 지원
- **외부 링크 불가**: URL 링크는 지원하지 않음 (카드형 응답 사용 필요)

---

## 커스터마이징

### 버튼 추가/제거

**`webhook_server.py`의 `_get_default_quick_replies()` 수정**:
```python
def _get_default_quick_replies(self) -> list:
    return [
        {
            'action': 'message',
            'label': '💰 골드',
            'messageText': '골드'
        },
        # 새로운 버튼 추가
        {
            'action': 'message',
            'label': '🎯 새 기능',
            'messageText': '새기능'
        },
        # ... 기존 버튼들
    ]
```

### 게임별 Quick Replies 추가

**새로운 게임 Quick Replies 생성**:
```python
def _get_number_guess_quick_replies(self) -> list:
    """숫자맞추기 게임 Quick Replies"""
    return [
        {
            'action': 'message',
            'label': '1',
            'messageText': '1'
        },
        {
            'action': 'message',
            'label': '50',
            'messageText': '50'
        },
        {
            'action': 'message',
            'label': '100',
            'messageText': '100'
        },
        {
            'action': 'message',
            'label': '❌ 종료',
            'messageText': '게임종료'
        }
    ]
```

**게임 상태에 따라 선택**:
```python
if game.__class__.__name__ == 'NumberGuessGame':
    quick_replies = self._get_number_guess_quick_replies()
elif game.__class__.__name__ == 'AdventureGame':
    quick_replies = self._get_adventure_quick_replies()
```

---

## 문제 해결

### 버튼이 표시되지 않는 경우

1. **응답 형식 확인**
   - `quickReplies` 필드가 올바르게 포함되어 있는지 확인
   - JSON 형식이 올바른지 확인

2. **카카오톡 버전 확인**
   - 최신 버전의 카카오톡 사용
   - Quick Replies는 최신 버전에서만 지원

3. **스킬 서버 로그 확인**
   - 응답에 `quickReplies`가 포함되어 있는지 확인
   - 버튼 개수가 10개 이하인지 확인

### 버튼 클릭 시 작동하지 않는 경우

1. **messageText 확인**
   - `messageText`가 올바른 명령어인지 확인
   - 명령어가 게임 엔진에서 인식되는지 확인

2. **스킬 서버 로그 확인**
   - 버튼 클릭 시 요청이 올바르게 전달되는지 확인
   - `utterance` 필드에 올바른 메시지가 포함되는지 확인

---

## 요약

### Quick Replies 기능

✅ **구현 완료**:
- 기본 Quick Replies 버튼 (골드, 게임시작, 랭킹 등)
- 모험 게임 Quick Replies 버튼 (강화, 사냥, 판매 등)
- 게임 상태에 따라 자동으로 버튼 변경

✅ **사용 방법**:
- 봇 멘션(`@게임봇`) 시 자동으로 버튼 표시
- 일반 메시지 응답 시에도 버튼 표시
- 버튼 클릭 시 해당 명령어 자동 전송

✅ **커스터마이징**:
- `webhook_server.py`에서 버튼 추가/제거 가능
- 게임별로 다른 버튼 세트 설정 가능

이제 카카오톡에서 봇을 멘션하면 이미지처럼 커맨드 버튼이 자동으로 표시됩니다! 🎉

