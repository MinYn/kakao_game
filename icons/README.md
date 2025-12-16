# 아이콘 디렉토리

이 디렉토리에 게임에서 사용할 아이콘 이미지를 저장하거나, Font Awesome 폰트를 설치할 수 있습니다.

## Font Awesome 사용 (권장)

Font Awesome Free를 사용하면 폰트 파일만 설치하면 자동으로 아이콘이 표시됩니다.

### 설치 방법

1. **Font Awesome 7 Free 다운로드**
   - URL: https://fontawesome.com/download
   - "Free for Desktop" 선택
   - 또는 GitHub에서 다운로드: https://github.com/FortAwesome/Font-Awesome/releases
   - npm 설치: `npm install @fortawesome/fontawesome-free`

2. **폰트 파일 설치**
   - Windows: `fa-solid-900.ttf` 또는 `Font Awesome 7 Free-Solid-900.otf` 파일을
     - `C:/Windows/Fonts/` 폴더에 복사
     - 또는 `icons/fonts/` 폴더에 저장
   - Linux: `/usr/share/fonts/truetype/fontawesome/` 또는 `icons/fonts/` 폴더에 저장
   - macOS: `/Library/Fonts/` 또는 `icons/fonts/` 폴더에 저장

3. **사용 가능한 아이콘**
   - `coin` - fa-coins (골드 아이콘) ✅
   - `coins` - fa-coins
   - `money` - fa-money-bill
   - `dollar` - fa-dollar-sign
   - `gold` - fa-coins
   - `treasure` - fa-treasure-chest
   - `gem` - fa-gem

## 이미지 파일 사용 (대안)

Font Awesome 폰트가 없을 경우 이미지 파일을 사용할 수 있습니다.

### 필요한 아이콘

- **coin.png** (또는 coin.jpg): 골드/금화 아이콘
  - 권장 크기: 24x24px ~ 64x64px
  - 투명 배경(PNG) 권장

### 지원하는 파일 형식

- PNG (권장, 투명 배경 지원)
- JPG/JPEG

### 무료 아이콘 팩 추천

1. **Font Awesome** (이미지로 변환)
   - URL: https://fontawesome.com
   - 무료 버전 사용 가능
   - SVG를 PNG로 변환하여 사용

2. **Flaticon**
   - URL: https://www.flaticon.com
   - 무료 계정으로 제한적 사용 가능
   - 검색어: "coin", "gold", "money"

3. **Icons8**
   - URL: https://icons8.com
   - 무료 아이콘 제공
   - 검색어: "coin", "gold coin"

4. **Material Icons**
   - URL: https://fonts.google.com/icons
   - Google의 무료 아이콘
   - 검색어: "monetization_on", "attach_money"

5. **Heroicons**
   - URL: https://heroicons.com
   - MIT 라이선스
   - SVG를 PNG로 변환하여 사용

## 사용 방법

### Font Awesome 사용 (권장)
1. Font Awesome 폰트 파일 설치
2. 게임 실행 시 자동으로 아이콘이 표시됩니다

### 이미지 파일 사용
1. 위 사이트에서 원하는 아이콘 다운로드
2. `coin.png` (또는 `coin.jpg`)로 파일명 변경
3. 이 디렉토리에 저장
4. 게임 실행 시 자동으로 아이콘이 표시됩니다

## 우선순위

1. Font Awesome 폰트 (설치되어 있으면 자동 사용)
2. 이미지 파일 (`coin.png`, `coin.jpg` 등)
3. 아이콘이 없으면 텍스트만 표시

