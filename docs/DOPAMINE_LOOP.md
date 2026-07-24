# Dopamine Loop (이슈 #19)

도파민 드리븐 개발(DDD) 적용 요약. 기능 추가보다 **짧은 피드백 · 가변 보상 · near-miss · CTA** 를 우선한다.

## 코어 루프

```text
짧은 루프 (~30초)
  출동 → 성공/실패/득템/기체? → 골드↑ → 강화 유혹 → 재탭

중간 루프 (세션)
  +N 구간 돌파 · 등급 승급 임박 · 도감 빈칸

긴 루프 (수집/시즌)
  F→S · 파츠 +N · 배지 티어
```

역할:
- **출동** = 메인 가변 보상
- **강화** = 하이리스크 피크
- **도감** = 수집 피크
- **상태/골드/패스** = 결과 표시

코드 상수: `config.Config` (`MISSION_*`, `ENHANCE_*`, `DUPLICATE_SHIP_GOLD`, `DAILY_*`)  
템플릿: `ui/result_template.py` (`build_detail_slots`)  
화면 CTA: `ui/screens.py` (`LOOP_RESULT_SCREEN_IDS`)

## DETAIL 슬롯 (15×25)

```
훅 → 수치 변화 → 보너스/드랍 → 진행(비용·성공률) → 한 번 더
```

## D2 결과 버튼 (루프 유지, 홈 강제 해제)

| 화면 | 버튼 2 |
|------|--------|
| 출동 결과 | `[다시 출동][강화 ·성공률%]` |
| 강화 결과 | `[다시 강화 ·% ][출동]` |
| 정산 결과 | `[강화][출동]` |

홈(D0)은 메뉴·명시 슬롯으로 진입. #17 depth 문서와 동기화: **CTA 우선**.

## 보호 보상

| 상황 | 처리 |
|------|------|
| 출동 실패 | 구조금 + soft pity (연속 실패 시 성공률↑) |
| 도감 중복 | 등급별 골드 (완전 꽝 금지) |
| 신규 기체 | NEW 피크 연출 |
| 강화 near-miss | 본체 유지 + pity |
| 강화 +5/+10… | 마일스톤 연출 + 배지 stage |

## 일일 미니 목표

홈 1줄: `📅 출동 N/5 강화 M/3` (`DAILY_MISSION_GOAL` / `DAILY_ENHANCE_GOAL`)

## 계측

`events/telemetry.py` 이벤트:

- `mission_result` (success/fail/reward)
- `enhance_result` (margin/celebration/near_miss)
- `ship_drop` (grade/is_new)
- `button_click` / `screen_id`
- `session_retap` (같은 루프 CTA 연속)

로그 + (옵션) Kafka `game-events`.

## 레이아웃 가드 (#17)

- DETAIL: ≤15줄 × ≤25자, 버튼 2
- MENU: ≤5줄 × ≤25자, 버튼 4
- 과장·다크 패턴 절망 루프 금지 (보호 보상 병행)
