# 완전 무료로 카카오톡 챗봇 사용하기

## 개요

**완전 무료**로 카카오톡 챗봇을 사용하는 방법을 안내합니다. API 호출 제한 없이 사용 가능합니다!

## 방법 1: 카카오 챗봇 관리자센터 사용 (완전 무료, 추천) ⭐

### 장점
- **완전 무료**: API 제한 없음
- 실제 카카오톡으로 메시지 전송
- Docker 불필요
- FastAPI만 설치하면 됨

### 사용 방법
1. 카카오 챗봇 관리자센터 접속: https://i.kakao.com/
2. 챗봇 생성 및 스킬 등록
3. 웹훅 서버 실행: `python main.py kakao`
4. 스킬 서버 URL 등록

### 상세 가이드
- 자세한 설정 방법: `CHATBOT_ADMIN_GUIDE.md` 참조

## 방법 2: 웹훅 서버 직접 구축 (완전 무료) ⭐ 추천

### 장점
- **완전 무료**: 카카오 챗봇 관리자센터의 무료 기능 활용
- **API 호출 제한 없음**: 제한 없음
- 직접 제어 가능
- Docker 불필요

### 단점
- 웹훅 서버 구축 필요
- 공개 서버 또는 ngrok 등 터널링 서비스 필요 (무료 옵션 많음)

### 설정 방법

#### 1. 카카오톡 비즈니스 채널 생성

1. **카카오톡 비즈니스 접속**
   ```
   https://business.kakao.com/
   ```

2. **채널 생성**
   - 채널 이름, 프로필 설정
   - 무료로 생성 가능

3. **챗봇 활성화**
   - 채널 관리 → 챗봇 설정
   - 챗봇 활성화

#### 2. 웹훅 서버 구축

**로컬 개발 (ngrok 사용):**

```bash
# ngrok 설치
brew install ngrok  # macOS
# 또는 https://ngrok.com/download

# 웹훅 서버 실행
python main.py kakao

# 다른 터미널에서 ngrok 실행
ngrok http 5000
```

ngrok이 제공하는 URL 예시:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:5000
```

**서버 배포 (무료 호스팅 서비스):**

- **Heroku**: https://www.heroku.com/ (무료 티어 제공)
- **Railway**: https://railway.app/ (무료 크레딧 제공)
- **Render**: https://render.com/ (무료 티어 제공)
- **PythonAnywhere**: https://www.pythonanywhere.com/ (무료 티어 제공)

#### 3. 카카오톡 비즈니스 채널에 웹훅 등록

**상세한 단계별 가이드는 `KAKAO_BUSINESS_SETUP.md` 파일을 참조하세요.**

간단 요약:
1. **카카오 비즈니스 접속**: https://business.kakao.com/
2. **채널 생성** (처음 사용하는 경우)
3. **챗봇 설정** → 챗봇 활성화
4. **API 연동** → 웹훅 URL 입력: `https://abc123.ngrok.io/webhook`
5. **연결 확인**

자세한 스크린샷과 단계별 설명은 `KAKAO_BUSINESS_SETUP.md` 참조

#### 4. 실행

**웹훅 서버 모드로 실행:**

```bash
# 웹훅 서버 모드로 실행 (완전 무료)
python main.py kakao
```

**로컬 테스트 (ngrok 사용):**

```bash
# 터미널 1: 웹훅 서버 실행
python main.py kakao

# 터미널 2: ngrok 실행
ngrok http 5000
```

ngrok이 제공하는 URL을 카카오톡 비즈니스 채널에 등록하세요.

## 방법 3: CLI 모드만 사용 (완전 무료)

### 장점
- **완전 무료**: API 호출 없음
- 빠른 개발/테스트
- 모든 게임 기능 사용 가능

### 사용 방법

```bash
# CLI 모드 실행
python main.py cli
# 또는
python cli.py
```

### 특징
- 실제 카카오톡으로 메시지 전송 안 함
- 콘솔에서 모든 기능 테스트 가능
- 게임 로직 개발 및 테스트에 최적


## 비교표

| 방법 | 비용 | 실제 전송 | API 제한 | 설정 난이도 | 추천도 |
|------|------|-----------|----------|------------|--------|
| **카카오 챗봇 관리자센터** | **완전 무료** | ✅ | **제한 없음** | 중 | ⭐⭐⭐⭐⭐ |
| CLI 모드 | 완전 무료 | ❌ | 없음 | 낮음 | ⭐⭐⭐⭐⭐ |

## 추천 방법

### 완전 무료로 사용하려면 ⭐
→ **카카오 챗봇 관리자센터 사용** (완전 무료, API 제한 없음)
- 카카오 챗봇 관리자센터 무료 기능 활용
- ngrok 또는 무료 호스팅 서비스 사용
- `python main.py kakao` 실행
- 상세 가이드: `CHATBOT_ADMIN_GUIDE.md` 참조

### 개발/테스트 단계
→ **CLI 모드** 사용 (완전 무료, 빠른 개발)

## 웹훅 서버 구축 상세 가이드

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

또는 직접 설치:
```bash
pip install fastapi uvicorn
```

### 2. 실행

**웹훅 서버 모드로 실행:**

```bash
# 웹훅 서버 모드 (완전 무료)
python main.py kakao
```

이렇게 하면 웹훅 서버가 실행됩니다.

### 3. 무료 호스팅 서비스 배포

**Railway 예시 (무료 크레딧 제공):**

```bash
# Railway CLI 설치
npm i -g @railway/cli

# 로그인
railway login

# 프로젝트 초기화
railway init

# 배포
railway up
```

**Render 예시 (무료 티어):**

1. https://render.com/ 접속
2. New Web Service 선택
3. GitHub 저장소 연결
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python main.py kakao`
6. Deploy

**ngrok 사용 (로컬 개발, 완전 무료):**

```bash
# ngrok 설치
brew install ngrok  # macOS
# 또는 https://ngrok.com/download

# 웹훅 서버 실행
python main.py kakao

# 다른 터미널에서 ngrok 실행
ngrok http 5000
```

ngrok이 제공하는 URL을 카카오톡 비즈니스 채널에 등록하면 완전 무료로 사용 가능합니다!

## FAQ

**Q: 완전 무료로 사용할 수 있나요?**
A: 네! 웹훅 서버 모드를 사용하면 완전 무료로 사용할 수 있습니다. `python main.py kakao --webhook` 실행 후 ngrok이나 무료 호스팅 서비스를 사용하세요.

**Q: 가장 무료로 사용하는 방법은?**
A: 웹훅 서버 구축입니다. 카카오톡 비즈니스 채널의 무료 기능을 활용하므로 API 제한이 없습니다.

**Q: 웹훅 서버 구축이 어렵나요?**
A: `python main.py kakao --webhook` 명령어만 실행하면 됩니다. ngrok을 사용하면 로컬에서도 쉽게 테스트 가능합니다.

**Q: 웹훅 서버는 정말 무료인가요?**
A: 네! 카카오 챗봇 관리자센터의 기본 기능은 완전 무료입니다. 서버 호스팅도 ngrok(무료)이나 Railway/Render(무료 티어)를 사용하면 비용이 발생하지 않습니다.

**Q: Docker 없이도 사용할 수 있나요?**
A: 네! 웹훅 서버 모드를 사용하면 Docker 없이도 사용할 수 있습니다. FastAPI만 설치하면 됩니다.

**Q: API 제한이 있나요?**
A: 없습니다! 카카오 챗봇 관리자센터를 사용하면 API 제한 없이 완전 무료로 사용할 수 있습니다.

