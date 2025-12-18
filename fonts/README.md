# 폰트 설치 가이드

## Docker 컨테이너 폰트

Dockerfile에 다음 폰트들이 자동으로 설치됩니다:

- **Noto Sans CJK**: 한글, 중국어, 일본어 지원
- **Noto Color Emoji**: 이모지 지원
- **Nanum**: 나눔고딕, 나눔코딩
- **DejaVu Sans**: 기본 라틴 문자 폰트

## Font Awesome 폰트 (선택사항)

이미지 생성 시 아이콘을 사용하려면 Font Awesome 폰트를 추가할 수 있습니다.

### 설치 방법

1. **Font Awesome 다운로드**
   - https://fontawesome.com/download
   - Font Awesome 7 Free 다운로드

2. **폰트 파일 복사**
   ```bash
   # fonts 디렉토리 생성
   mkdir -p fonts
   
   # Font Awesome 폰트 파일 복사
   # 다운로드한 파일에서 fa-solid-900.ttf 또는 Font Awesome 7 Free-Solid-900.otf 복사
   cp fa-solid-900.ttf fonts/
   ```

3. **Dockerfile 수정** (선택사항)
   ```dockerfile
   # Font Awesome 폰트 복사
   COPY fonts/ /usr/share/fonts/truetype/fontawesome/
   RUN fc-cache -fv
   ```

또는 볼륨 마운트로 사용:
```yaml
volumes:
  - ./fonts:/usr/share/fonts/truetype/fontawesome:ro
```

## 폰트 확인

컨테이너 내에서 폰트 확인:

```bash
# 설치된 폰트 목록 확인
docker-compose exec gamebot fc-list | grep -i "noto\|nanum"

# 폰트 캐시 새로고침
docker-compose exec gamebot fc-cache -fv
```

## 문제 해결

### 한글이 깨져서 표시됨

1. 폰트가 제대로 설치되었는지 확인
2. 폰트 캐시 새로고침: `fc-cache -fv`
3. 컨테이너 재시작

### Font Awesome 아이콘이 표시되지 않음

1. `fonts/` 디렉토리에 폰트 파일이 있는지 확인
2. Dockerfile에 폰트 복사 명령 추가
3. 이미지 재빌드: `docker-compose build`
