from pathlib import Path

from image_generator import ImageGenerator


SIMPLE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <rect width="16" height="16" fill="#ff8fab" />
</svg>
""".strip()


def test_generate_svg_image_reuses_cached_png(tmp_path: Path):
    generator = ImageGenerator(output_dir=str(tmp_path), icons_dir=str(tmp_path / "icons"))

    first_path = generator.generate_svg_image(SIMPLE_SVG, filename_prefix="badge")
    second_path = generator.generate_svg_image(SIMPLE_SVG, filename_prefix="badge")

    assert first_path == second_path
    assert Path(first_path).exists()
    assert Path(first_path).parent == tmp_path / "image_cache"


def test_generate_svg_gif_reuses_cached_gif(tmp_path: Path):
    generator = ImageGenerator(output_dir=str(tmp_path), icons_dir=str(tmp_path / "icons"))

    first_path = generator.generate_svg_gif([SIMPLE_SVG, SIMPLE_SVG], filename_prefix="badge")
    second_path = generator.generate_svg_gif([SIMPLE_SVG, SIMPLE_SVG], filename_prefix="badge")

    assert first_path == second_path
    assert Path(first_path).exists()
    assert Path(first_path).suffix == ".gif"
