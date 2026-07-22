# 기체 등급 체계 마이그레이션 (#15)

## 요약

단일 `enhancement_levels.level` 을 아래 4축으로 분리한다.

| 축 | 필드 | 설명 |
|----|------|------|
| 기체 등급 | `ship_grade` | F ~ S (파츠 등급 아님) |
| 본체 강화 | `body_enhance` (+ `level` 동기화) | +0 ~ +N |
| 파츠 강화 | `part_engine`, `part_sensor`, `part_armor` | 등급 없음, 패시브 +N |
| 장착 기체 | `equipped_ship_id` | 도감 ship_id |

## 기존 유저 정책

기동 시 스키마 마이그레이션:

1. 신규 컬럼 추가 (기본값 `ship_grade='F'`, `body_enhance=0`, 파츠 0)
2. `body_enhance` 컬럼을 **실제로 추가한 최초 1회에만** `level → body_enhance` 복사
3. 이후 `body_enhance` 를 원본으로 삼아 `level` 을 단방향 동기화 (API/구 코드 호환)

매 기동마다 `level → body_enhance` 를 재실행하지 않는다. 따라서 정산 후
`body_enhance=0`인 행이 과거 `level` 값 때문에 다시 강화 상태로 복원되지 않는다.
직접 복구한 레코드에는 `ShipProgress.from_record()`의 레거시 폴백을 사용할 수 있지만,
마이그레이션이 끝난 SQLite/Postgres 저장소는 `body_enhance`를 권위 값으로 읽는다.

코드 진입점: `games/ship_system.migrate_legacy_level`, `GoldSystem._ensure_enhancement_columns`, `PostgreSQLManager._ensure_enhancement_columns`.

## 도감 희귀도 제거

| 제거 | 대체 |
|------|------|
| `CollectibleShip.rarity` (`common`…`mythic`) | `CollectibleShip.grade` (`F`…`S`) |
| `ShipRarity` / `_init_ship_rarities` | `GRADE_DROP_WEIGHTS` (F 흔함 → S 희귀) |
| 도감 섹션 `⚪ 일반` | `F 3/3 · 입문 기체` 형태 |
| 발견 메시지 `🔵 희귀 [이름]` | `등급 E [이름]` |

레거시 문자열 매핑: `migrate_legacy_rarity()`  
(`common→F`, `rare→E`, `epic→C`, `legendary→A`, `mythic→S`)

카탈로그 매핑(현행):

| ship_id | grade |
|---------|-------|
| comet_scout, cargo_mule, lunar_moth | F |
| ion_falcon | E |
| nebula_ray, aurora_clip | D |
| quantum_fox | C |
| void_manta | B |
| solar_dragon | A |
| event_horizon | S |

## 등가 계승 앵커

```
stat(grade, n) = base(grade) + n * per_level(grade)
base(grade) = grade_index * 99
per_level = 1.0  (전 등급 동일, 튜닝 시 계수만 변경)

F+100 ≈ E+1
E+100 ≈ D+1
… (연속 등급 동일 곡선)
```

단위 테스트: `tests/test_ship_system.py`.

성공률과 임무 보상도 raw `body_enhance`가 아닌 위 등가 스탯을 사용한다.
따라서 F+100 → E+1 계승 전후의 실제 플레이 효과가 유지된다.

## 파츠 영구 성장 정책

- 본체 강화 성공 시 엔진/센서/장갑 중 하나가 +1 성장한다.
- 파츠 +N은 강화 실패나 정산으로 감소하지 않는 영구 성장 축이다.
- 정산은 본체 `body_enhance`만 0으로 만들며 등급, 장착 기체, 파츠 +N은 유지한다.
- 현재 버전은 파츠 +N 자체에 상한을 두지 않는다. 다만 성공률은 전체 98%,
  장갑의 실패 보호 발동률은 25%로 제한된다.

## 배지 비주얼

- `upgrade_stage_from_attempts` → **`body_enhance` 구간** (0 / 5 / 15 / 30 → stage 0~3)
- 배지에 **등급 문자 마크** (F~S)

## 롤백

컬럼을 남겨 두어도 구 `level` 읽기 경로는 `get_enhancement_level` → `body_enhance` 로 동작한다.
완전 롤백 시 `body_enhance` 값을 `level` 로 복사한 뒤 신규 컬럼 사용을 중단하면 된다.
