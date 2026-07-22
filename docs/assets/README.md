# Preview assets

- [`pixel_ship_badge_preview.svg`](pixel_ship_badge_preview.svg) — 초기 픽셀 배지 프리뷰
- [`ship_samples/`](ship_samples/) — 이슈 #15 기체 샘플 (shape / 등급 F~S / 본체 +N / 도감 예시)

SVG와 PNG를 함께 커밋합니다. GitHub PR에서 PNG 미리보기가 가능합니다.

To render a local PNG preview when needed:

```bash
python - <<'PY'
from pathlib import Path
import cairosvg

svg_path = Path('docs/assets/pixel_ship_badge_preview.svg')
png_path = Path('docs/assets/pixel_ship_badge_preview.local.png')
cairosvg.svg2png(
    bytestring=svg_path.read_bytes(),
    write_to=str(png_path),
    output_width=512,
    output_height=512,
)
print(png_path)
PY
```

## PR preview snippet

Add this snippet to the pull request description to display the SVG preview without committing a binary PNG:

```markdown
### Example image

![Pixel-art spaceship badge preview](docs/assets/pixel_ship_badge_preview.svg)
```
