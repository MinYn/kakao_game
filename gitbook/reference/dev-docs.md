# 개발자 문서 링크

플레이어 공략이 아닌 **운영·개발** 문서입니다. 레포 안 경로.

| 문서 | 내용 |
|------|------|
| [`docs/DOPAMINE_LOOP.md`](../../docs/DOPAMINE_LOOP.md) | #19 루프·CTA·계측 설계 |
| [`docs/SHIP_GRADE_MIGRATION.md`](../../docs/SHIP_GRADE_MIGRATION.md) | #15 등급 체계 |
| [`docs/CODE_OVERVIEW.md`](../../docs/CODE_OVERVIEW.md) | 코드 구조 |
| [`docs/COMMAND_API_GUIDE.md`](../../docs/COMMAND_API_GUIDE.md) | 커맨드 API |
| [`docs/DOCKER.md`](../../docs/DOCKER.md) | Docker |
| [`README.md`](../../README.md) | 프로젝트 루트 README |

## GitBook 게시

레포 루트 `.gitbook.yaml`:

```yaml
root: ./gitbook
```

1. [GitBook](https://www.gitbook.com/) 스페이스 생성  
2. GitHub 동기화 → 이 레포 연결  
3. monorepo root 설정이 `./gitbook` 인지 확인  
4. `SUMMARY.md` 가 사이드바 목차  

로컬 미리보기 (선택, `@gitbook/cli` 등 툴체인 사용 시):

```bash
# 예: GitBook 레거시 CLI 또는 공식 Git Sync
# 문서 루트는 gitbook/
```

## 코드 상수 위치

| 관심사 | 파일 |
|--------|------|
| 튜닝 숫자 | `config.py` |
| 출동·강화 로직 | `games/adventure.py` |
| 등급·파츠 | `games/ship_system.py` |
| 화면·CTA 버튼 | `ui/screens.py` |
| 결과 슬롯 | `ui/result_template.py` |
| 텔레메트리 | `events/telemetry.py` |
