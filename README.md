# GameBot - 채팅 게임 봇

채팅 플랫폼에 연동 가능한 게임 봇입니다. 현재는 디스코드(및 로컬 CLI 테스트)에 집중해 우주 탐험 로그 경험을 제공합니다.

## 구조

```
kakao_game/
├── games/              # 게임 로직
│   ├── base_game.py    # 게임 기본 클래스
│   └── adventure.py    # 우주 탐험 로그 게임 (우주선 강화 + 임무)
├── platforms/          # 채팅 플랫폼 어댑터
│   ├── base_platform.py    # 플랫폼 기본 인터페이스
│   └── discord_adapter.py  # 디스코드 어댑터
├── game_engine.py      # 게임 엔진
├── point_system.py     # 골드 관리 시스템
├── main.py             # 메인 실행 파일
├── requirements.txt    # 의존성
├── Dockerfile               # Docker 이미지 정의
├── docker-compose.yml      # Docker Compose 설정
├── .dockerignore           # Docker 빌드 제외 파일
├── docs/                    # 문서 폴더
│   ├── USER_UTTERANCE.md        # 사용자 발화 설정 가이드 (모든 발화, 커맨드 형태) ⭐
│   ├── QUICK_REPLIES.md         # Quick Replies 버튼 가이드 ⭐
│   ├── PARAMETER_GUIDE.md       # 파라미터 설정 상세 가이드
│   ├── TROUBLESHOOTING.md       # 문제 해결 가이드 ⚠️
│   ├── DOCKER.md                # Docker 사용 가이드
│   └── FREE_SETUP.md            # 무료 사용 가이드
```

## 사용법

### 기본 실행

**로컬 실행:**

```bash
# CLI 테스트 모드 (로컬에서 테스트)
python main.py cli
# 또는
python cli.py

# 디스코드 모드
python main.py discord
```

**Docker 사용 (선택사항):**

```bash
# Docker 이미지 빌드
docker-compose build

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 컨테이너 중지
docker-compose down

# 볼륨 포함 삭제 (데이터도 삭제)
docker-compose down -v
```

**볼륨 관리:**
- 데이터베이스는 명명된 볼륨(`gamebot_data`)에 저장됩니다
- 로그는 `gamebot_logs` 볼륨에 저장됩니다
- 자세한 내용은 `docs/DOCKER.md` 참조

### CLI 모드 사용법

CLI 모드에서는 로컬에서 게임을 테스트할 수 있습니다:

```bash
python cli.py
```

**주요 명령어:**
- `게임목록`: 사용 가능한 게임 보기
- `게임시작 모험`: 우주 탐험 게임 시작 (우주선 강화 + 임무)
- `골드`: 내 골드 조회
- `골드주기 [사용자] [금액]`: 다른 사용자에게 골드 전송
- `리더보드`: 골드 랭킹 보기
- `사용자 [이름]`: 사용자 변경
- `도움말`: 명령어 도움말
- `종료`: 프로그램 종료

### 게임 명령어

- `골드`: 내 골드 조회
- `골드주기 [사용자] [금액]`: 다른 사용자에게 골드 전송
- `리더보드`: 골드 랭킹 보기
- `게임목록`: 사용 가능한 게임 목록 보기
- `게임시작 모험`: 우주 탐험 게임 시작 (우주선 강화 + 임무)
- `게임종료`: 현재 게임 종료
- `도움말`: 도움말 보기

### 골드 시스템

모든 게임에서 골드를 획득하거나 사용할 수 있습니다.

**우주 탐험 로그 게임 (우주선 강화 + 임무):**
- 사용자별 고유 탐사대 프로필과 기체 배지가 로컬 결정적으로 생성됩니다 (추가 요금 없음).
- 우주선 강화를 통해 임무 보상 배율이 상승하며, 정산 시 투자 골드를 회수할 수 있습니다.
- 임무: 정찰(기본), 탐사(패스 드랍), 구조(패스 소모)로 골드를 획득합니다.
- 패스: 탐사 임무에서 일정 확률로 구조 패스를 얻어 고보상 구조 임무를 시도합니다.

골드는 PostgreSQL 데이터베이스에 저장되며, 모든 트랜잭션이 Kafka를 통해 이벤트로 발행됩니다.

## 게임 추가하기

1. `games/` 폴더에 새 게임 파일 생성
2. `Game` 클래스를 상속받아 구현:

```python
from games.base_game import Game

class MyGame(Game):
    def __init__(self, user_id: str, point_system=None):
        super().__init__(user_id, point_system)
    
    def start(self) -> str:
        # 게임 시작 로직
        # 골드 차감 예시:
        # if self.point_system:
        #     self.deduct_points(10, "게임 입장료")
        pass
    
    def process_command(self, command: str) -> str:
        # 명령 처리 로직
        # 골드 지급 예시:
        # if self.point_system:
        #     self.award_points(50, "게임 클리어")
        pass
    
    def get_help(self) -> str:
        # 도움말 반환
        pass
```

3. `game_engine.py`의 `available_games`에 추가

**골드 시스템 사용:**
- `self.award_points(amount, reason)`: 골드 지급
- `self.deduct_points(amount, reason)`: 골드 차감
- `self.get_user_points()`: 사용자 골드 조회

## 플랫폼 추가하기

1. `platforms/` 폴더에 새 어댑터 파일 생성
2. `ChatPlatform` 클래스를 상속받아 구현:

```python
from platforms.base_platform import ChatPlatform

class MyPlatformAdapter(ChatPlatform):
    def send_message(self, user_id: str, message: str) -> bool:
        # 메시지 전송 로직
        pass
    
    def start(self) -> None:
        # 플랫폼 시작 로직
        pass
    
    def stop(self) -> None:
        # 플랫폼 종료 로직
        pass
```

3. `main.py`의 `_create_platform`에 추가

## 실제 연동 방법

현재는 **디스코드 봇** 연동만 지원합니다. 디스코드 개발자 포털에서 봇 토큰을 발급한 후 `.env`에 `DISCORD_TOKEN`을 넣고 다음 명령어로 실행하세요:

```bash
python main.py discord
```

**서버 배포 환경:**
- 공개 서버의 도메인 사용 (예: `https://yourdomain.com/webhook`)
- HTTPS 필수

#### 3. .env 파일 설정 (선택사항)

`.env` 파일에 다음 값 설정 (선택사항):
```env
PLATFORM=discord
INITIAL_POINTS=100
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

**참고**: `KAKAO_API_KEY`는 더 이상 필요 없습니다!

#### 5. 실행 및 테스트

**로컬 실행:**

```bash
# 패키지 설치
pip install -r requirements.txt

# 웹훅 서버 모드로 실행 (완전 무료)
python main.py discord
```

**웹훅 서버 모드 (완전 무료):**
- 카카오 챗봇 관리자센터 스킬 서버로 동작
- API 제한 없음
- ngrok 또는 무료 호스팅 서비스 사용
- Docker 불필요

**추천 방법:**
- **카카오 챗봇 관리자센터 사용** (완전 무료, 추천!)
  - 상세 가이드: `docs/CHATBOT_ADMIN_GUIDE.md` 참조
  - 스킬 서버로 연동하여 모든 게임 기능 사용 가능

카카오톡 채널에서 메시지를 보내면 봇이 응답합니다.

**필수 설정:**
- FastAPI 설치: `pip install fastapi uvicorn`
- 카카오 챗봇 관리자센터에서 스킬 서버 URL 등록
- 자세한 설정: `docs/CHATBOT_ADMIN_GUIDE.md` 참조

**과금 정보:**
- **완전 무료**: 카카오 챗봇 관리자센터의 무료 기능 활용
- API 제한 없음
- 서버 호스팅만 필요 (ngrok 무료 또는 무료 호스팅 서비스 사용)

자세한 설정 및 무료 사용 방법은 `docs/CHATBOT_ADMIN_GUIDE.md`와 `docs/FREE_SETUP.md` 참조

### 디스코드

디스코드 봇을 사용하려면:

#### 1. Discord Developer Portal에서 봇 생성

1. **Discord Developer Portal 접속**
   - https://discord.com/developers/applications 접속
   - Discord 계정으로 로그인

2. **새 애플리케이션 생성**
   - "New Application" 클릭
   - 애플리케이션 이름 입력 (예: "GameBot")
   - "Create" 클릭

3. **봇 생성**
   - 왼쪽 메뉴에서 "Bot" 클릭
   - "Add Bot" 클릭
   - "Yes, do it!" 클릭

4. **봇 토큰 복사**
   - "Token" 섹션에서 "Reset Token" 또는 "Copy" 클릭
   - 토큰을 안전하게 보관 (다시 볼 수 없으므로 복사 필수!)

5. **봇 권한 설정**
   - "Bot Permissions" 섹션에서 필요한 권한 선택:
     - Send Messages
     - Read Message History
     - Use Slash Commands (선택사항)
   - "OAuth2" → "URL Generator"에서 권한 선택 후 생성된 URL로 봇을 서버에 초대

#### 2. 환경 변수 설정

`.env` 파일에 다음 값 설정:

```env
PLATFORM=discord
DISCORD_TOKEN=your_bot_token_here
DISCORD_COMMAND_PREFIX=!
INITIAL_POINTS=100
```

**중요**: `DISCORD_TOKEN`에 위에서 복사한 봇 토큰을 입력하세요.

#### 3. 패키지 설치 및 실행

```bash
# 패키지 설치
pip install -r requirements.txt

# 디스코드 봇 실행
python main.py discord
```

#### 4. 사용 방법

- **DM (개인 메시지)**: 봇에게 직접 메시지를 보내면 자동으로 응답합니다.
- **서버 채널**: 명령어 접두사(`!`)를 사용하여 명령을 실행합니다.
  - 예: `!게임목록`, `!게임시작 모험`, `!골드` 등

**주요 명령어:**
- `!게임목록`: 사용 가능한 게임 보기
- `!게임시작 모험`: 우주 탐험 게임 시작 (우주선 강화 + 임무)
- `!골드`: 내 골드 조회
- `!골드주기 [사용자] [금액]`: 다른 사용자에게 골드 전송
- `!리더보드`: 골드 랭킹 보기
- `!도움말`: 도움말 보기

## 예시

```python
from game_engine import GameEngine
from platforms.discord_adapter import DiscordAdapter
from point_system import PointSystem

# 골드 시스템 생성 (선택사항 - GameEngine이 자동 생성)
point_system = PointSystem()

# 게임 엔진 생성 (골드 시스템과 함께)
engine = GameEngine(point_system=point_system)

# 플랫폼 생성 및 연결
platform = KakaoAdapter(api_key="your_api_key")
platform.set_message_handler(engine.process_message)

# 봇 시작
platform.start()
```

## 골드 시스템 API

```python
from point_system import PointSystem

ps = PointSystem()

# 골드 조회
gold = ps.get_points("user_id")

# 골드 추가
new_balance = ps.add_points("user_id", 100, "보너스")

# 골드 차감
new_balance = ps.deduct_points("user_id", 50, "아이템 구매")
# 잔액 부족 시 None 반환

# 골드 보유 여부 확인
has_enough = ps.has_points("user_id", 100)

# 리더보드 조회
top_10 = ps.get_leaderboard(10)
```
