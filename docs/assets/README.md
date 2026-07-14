# Preview assets

Binary image previews are intentionally not committed because this review environment may show
"binary files are not supported" for PNG files.

Use the SVG preview instead:

- [`pixel_ship_badge_preview.svg`](pixel_ship_badge_preview.svg)

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
