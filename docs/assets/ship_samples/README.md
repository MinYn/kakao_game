# Ship badge samples (issue #15)

`space_badges` 생성기로 뽑은 미리보기입니다. Discord 배지와 동일 파이프라인입니다.

## 구성

| 접두사 | 설명 |
|--------|------|
| `shape_*` | shape 4종 (shuttle / rocket / interceptor / lifter), 등급 F, +0 |
| `grade_*` | 등급 마크 F~S (동일 셔틀 실루엣) |
| `enhance_plus*` | 본체 +N → upgrade_stage 0~3 (S 로켓) |
| `catalog_*` | 도감 스타일 예시 (등급·강화 조합) |

SVG 원본과 렌더 PNG(512px)를 함께 둡니다.

## 재생성

```bash
# SVG (repo root)
PYTHONPATH=. python3 - <<'PY'
from pathlib import Path
from space_badges.registry import BadgeVariant, ShipShape
from space_badges.generator import generate_svg
from games.ship_system import GRADE_ORDER, body_enhance_to_upgrade_stage

out = Path("docs/assets/ship_samples")
# ... same generation as PR helper scripts ...
print(out)
PY

# PNG (requires @resvg/resvg-js)
# node -e "..."  # see session history or use cairosvg
```
