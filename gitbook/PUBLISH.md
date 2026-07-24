# 공략집 올리기 (GitHub Pages)

GitBook 없이 **GitHub Pages**로 공략집을 공개할 수 있습니다.

## 한 번만 설정

1. GitHub 레포 열기: `MinYn/kakao_game`
2. **Settings → Pages**
3. **Build and deployment → Source** 를 **GitHub Actions** 로 선택
4. 이 브랜치를 push 하거나 Actions 탭에서  
   **Deploy guide (GitHub Pages)** → **Run workflow**

## 주소

공개되면 대략 이런 형태입니다.

```text
https://minyn.github.io/kakao_game/
```

(계정/org 이름·Pages 경로에 따라 다를 수 있음. Settings → Pages 에 최종 URL 표시)

## 주의: private 레포 (Actions 빨간불 원인)

이 레포가 **private + Free** 이면 GitHub Pages API가 거부됩니다.

에러 예:

```text
Get Pages site failed ... Not Found
Your current plan does not support GitHub Pages for this repository.
```

| 상황 | 가능 여부 |
|------|-----------|
| GitHub Free + private | Pages **불가** → 워크플로는 **스킵(성공)** 처리 |
| GitHub Pro / Team 등 | private에서도 Pages 가능 |
| 레포를 **Public** 으로 | Free에서도 Pages 가능 |

게이머에게 링크를 뿌리려면:

1. 레포 전체를 **Public** 으로 바꾸거나  
2. 공략집만 따로 public 레포에 두거나  
3. 유료 플랜 사용  
4. 또는 Cloudflare Pages / Netlify 에 `gitbook/` 폴더 연결  

Public으로 바꾼 뒤:

1. **Settings → Pages → Source = GitHub Actions**  
2. Actions → **Deploy guide (GitHub Pages)** → Run workflow  
   (또는 `master`에 `gitbook/` 변경 push)  


## 로컬에서 미리보기

`gitbook` 폴더에서 아무 정적 서버나 켜면 됩니다.

```bash
cd gitbook
python3 -m http.server 8080
# 브라우저: http://localhost:8080
```

## GitBook 은?

선택 사항입니다. 같은 마크다운을 GitBook Sync 로도 쓸 수 있고,  
GitHub Pages(docsify)만으로도 충분합니다.
