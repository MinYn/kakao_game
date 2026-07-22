from __future__ import annotations

from functools import lru_cache
import random
from typing import Optional

from space_badges.registry import BadgeVariant, ShipShape
from space_badges.ships import InterceptorShip, LifterShip, RocketShip, ShuttleShip


SHIP_RENDERERS = {
    ShipShape.SHUTTLE: ShuttleShip(),
    ShipShape.ROCKET: RocketShip(),
    ShipShape.INTERCEPTOR: InterceptorShip(),
    ShipShape.LIFTER: LifterShip(),
}

# shape 별 기본 배경/프레임/대기 팔레트
_SHAPE_THEMES: dict[ShipShape, dict[str, object]] = {
    ShipShape.SHUTTLE: {
        "bg": ("#5b8def", "#8b5cf6", "#f472b6"),
        "frame": ("#93c5fd", "#f9a8d4", "#fde68a"),
        "ring": "#60a5fa",
        "ring_mid": "#dbeafe",
        "ring_dash": "#3b82f6",
        "atmosphere": "#93c5fd",
        "name_plate": "#1e3a5f",
        "name_fill": "#eff6ff",
        "name_stroke": "#0f172a",
    },
    ShipShape.ROCKET: {
        "bg": ("#fb923c", "#ef4444", "#b45309"),
        "frame": ("#fdba74", "#fde047", "#fca5a5"),
        "ring": "#f97316",
        "ring_mid": "#ffedd5",
        "ring_dash": "#ea580c",
        "atmosphere": "#fdba74",
        "name_plate": "#7c2d12",
        "name_fill": "#fff7ed",
        "name_stroke": "#431407",
    },
    ShipShape.INTERCEPTOR: {
        "bg": ("#6366f1", "#7c3aed", "#312e81"),
        "frame": ("#a5b4fc", "#c4b5fd", "#e9d5ff"),
        "ring": "#818cf8",
        "ring_mid": "#e0e7ff",
        "ring_dash": "#4f46e5",
        "atmosphere": "#a5b4fc",
        "name_plate": "#1e1b4b",
        "name_fill": "#eef2ff",
        "name_stroke": "#0f0a2a",
    },
    ShipShape.LIFTER: {
        "bg": ("#14b8a6", "#eab308", "#f97316"),
        "frame": ("#5eead4", "#fde047", "#fdba74"),
        "ring": "#2dd4bf",
        "ring_mid": "#ccfbf1",
        "ring_dash": "#0d9488",
        "atmosphere": "#fbbf24",
        "name_plate": "#134e4a",
        "name_fill": "#f0fdfa",
        "name_stroke": "#042f2e",
    },
}

# color 키로 배경/프레임 틴트 보정 (기체별 색 다양성)
_COLOR_BG_OVERRIDES: dict[str, tuple[str, str, str]] = {
    "white": ("#7dd3fc", "#c4b5fd", "#f9a8d4"),
    "silver": ("#94a3b8", "#64748b", "#475569"),
    "dark": ("#312e81", "#1e1b4b", "#0f172a"),
    "black": ("#1f2937", "#111827", "#030712"),
    "gold": ("#fbbf24", "#f59e0b", "#d97706"),
    "blue": ("#2563eb", "#1d4ed8", "#1e3a8a"),
    "orange": ("#fb923c", "#ea580c", "#c2410c"),
}

_COLOR_FRAME_OVERRIDES: dict[str, tuple[str, str, str]] = {
    "white": ("#e0f2fe", "#fce7f3", "#fef9c3"),
    "silver": ("#e2e8f0", "#cbd5e1", "#94a3b8"),
    "dark": ("#a5b4fc", "#c4b5fd", "#f0abfc"),
    "black": ("#9ca3af", "#6b7280", "#fbbf24"),
    "gold": ("#fde68a", "#fcd34d", "#fef3c7"),
    "blue": ("#93c5fd", "#60a5fa", "#bfdbfe"),
    "orange": ("#fdba74", "#fb923c", "#fed7aa"),
}

# 본체 +N 구간별 하단 숫자 플레이트 스타일
_ENHANCE_TEXT_STYLES: tuple[dict[str, object], ...] = (
    {  # 0–4
        "min": 0,
        "plate": "#94a3b8",
        "plate_hi": "#e2e8f0",
        "plate_edge": "#475569",
        "text": "#0f172a",
        "stroke": "#ffffff",
        "stroke_w": 0,
        "glow": False,
        "font_size": 16,
    },
    {  # 5–14
        "min": 5,
        "plate": "#22d3ee",
        "plate_hi": "#a5f3fc",
        "plate_edge": "#0e7490",
        "text": "#083344",
        "stroke": "#ecfeff",
        "stroke_w": 1,
        "glow": False,
        "font_size": 17,
    },
    {  # 15–29
        "min": 15,
        "plate": "#fbbf24",
        "plate_hi": "#fef08a",
        "plate_edge": "#b45309",
        "text": "#422006",
        "stroke": "#fffbeb",
        "stroke_w": 1,
        "glow": True,
        "font_size": 18,
    },
    {  # 30+
        "min": 30,
        "plate": "#f472b6",
        "plate_hi": "#fce7f3",
        "plate_edge": "#9d174d",
        "text": "#500724",
        "stroke": "#ffffff",
        "stroke_w": 2,
        "glow": True,
        "font_size": 20,
    },
)


def generate_svg(
    variant: BadgeVariant,
    index: int,
    star_seed: Optional[int] = None,
    upgrade_stage: int = 0,
    grade: str = "F",
    body_enhance: int = 0,
) -> str:
    return _build_svg(
        variant,
        index,
        star_seed=star_seed,
        frame_index=0,
        upgrade_stage=upgrade_stage,
        grade=grade,
        body_enhance=max(0, int(body_enhance)),
    )


def generate_svg_frames(
    variant: BadgeVariant,
    index: int,
    star_seed: Optional[int] = None,
    frame_count: int = 2,
    upgrade_stage: int = 0,
    grade: str = "F",
    body_enhance: int = 0,
) -> list[str]:
    enhance = max(0, int(body_enhance))
    return [
        _build_svg(
            variant,
            index,
            star_seed=star_seed,
            frame_index=frame,
            upgrade_stage=upgrade_stage,
            grade=grade,
            body_enhance=enhance,
        )
        for frame in range(frame_count)
    ]


def enhance_text_style(body_enhance: int) -> dict[str, object]:
    """본체 +N 에 따른 하단 숫자 텍스트/플레이트 스타일."""
    n = max(0, int(body_enhance))
    chosen = _ENHANCE_TEXT_STYLES[0]
    for style in _ENHANCE_TEXT_STYLES:
        if n >= int(style["min"]):
            chosen = style
    return chosen


def _theme_for(variant: BadgeVariant) -> dict[str, object]:
    base = dict(_SHAPE_THEMES.get(variant.shape, _SHAPE_THEMES[ShipShape.SHUTTLE]))
    if variant.color in _COLOR_BG_OVERRIDES:
        base["bg"] = _COLOR_BG_OVERRIDES[variant.color]
    if variant.color in _COLOR_FRAME_OVERRIDES:
        base["frame"] = _COLOR_FRAME_OVERRIDES[variant.color]
    # dark/black 은 이름판을 더 진하게
    if variant.color in {"dark", "black"}:
        base["name_plate"] = "#0b1020"
        base["name_fill"] = "#f8fafc"
    if variant.color == "gold":
        base["name_plate"] = "#78350f"
        base["name_fill"] = "#fffbeb"
    return base


@lru_cache(maxsize=1024)
def _build_svg(
    variant: BadgeVariant,
    index: int,
    star_seed: Optional[int],
    frame_index: int,
    upgrade_stage: int,
    grade: str = "F",
    body_enhance: int = 0,
) -> str:
    badge_id = f"badge_{index}"
    theme = _theme_for(variant)
    defs = _get_defs(badge_id, variant.color, theme)
    ship_path = _get_ship_path(
        variant.shape,
        badge_id,
        variant.color,
        frame_index,
        upgrade_stage,
    )
    star_random = random.Random(star_seed)
    upgrade_overlay = _get_upgrade_overlay(badge_id, upgrade_stage)
    grade_mark = _get_grade_mark(badge_id, grade)
    name_banner = _get_name_banner(badge_id, variant.name, theme)
    enhance_plate = _get_enhance_plate(badge_id, body_enhance, variant.sub)

    ring = theme["ring"]
    ring_mid = theme["ring_mid"]
    ring_dash = theme["ring_dash"]
    atmosphere = theme["atmosphere"]
    terrain_y = "462" if variant.shape == ShipShape.ROCKET else "374"
    ship_scale = "0.9" if variant.shape == ShipShape.ROCKET else "1.1"

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="w-full h-full" shape-rendering="crispEdges">
    {defs}

    <g clip-path="url(#clip_{badge_id})">
        <rect width="512" height="512" fill="url(#bg_{badge_id})" />
        <g fill="#ffffff" fill-opacity="0.95" shape-rendering="crispEdges">
            {_generate_stars(star_random, 14 + max(upgrade_stage, 0) * 2)}
        </g>
        <g opacity="0.55" shape-rendering="crispEdges">
            {_generate_pixel_clouds(badge_id)}
        </g>
        <path d="M-100 438 Q256 {terrain_y} 612 438 V512 H-100 Z"
              fill="{atmosphere}" fill-opacity="0.32" />
    </g>

    <g transform="translate(256, 268) scale({ship_scale})"
       filter="url(#shadow_{badge_id})">
        {ship_path}
    </g>

    {upgrade_overlay}

    <g shape-rendering="crispEdges">
        <circle cx="256" cy="256" r="238" fill="none" stroke="{ring}" stroke-width="12" />
        <circle cx="256" cy="256" r="226" fill="none" stroke="{ring_mid}" stroke-width="10" />
        <circle cx="256" cy="256" r="214" fill="none" stroke="{ring_dash}"
                stroke-width="8" stroke-dasharray="12 10" />
        <path d="M256 24 V48 M488 256 H464 M256 488 V464 M24 256 H48"
              stroke="#3b1d2f" stroke-width="8" opacity="0.45" />
    </g>

    {name_banner}
    {grade_mark}
    {enhance_plate}
</svg>
""".strip()


def _get_defs(badge_id: str, color: str, theme: dict[str, object]) -> str:
    hull_colors = {
        "white": ["#e0e0e0", "#ffffff", "#d0d0d0"],
        "silver": ["#7a7f8e", "#a0a5b0", "#606570"],
        "dark": ["#2a2a35", "#3a3a45", "#1a1a25"],
        "black": ["#1a1a1a", "#333333", "#000000"],
        "gold": ["#d4af37", "#fcf6ba", "#aa8822"],
        "blue": ["#112244", "#224488", "#001133"],
        "orange": ["#cc5500", "#ff7722", "#aa4400"],
    }.get(color, ["#e0e0e0", "#ffffff", "#d0d0d0"])

    bg = theme["bg"]
    frame = theme["frame"]
    assert isinstance(bg, tuple) and isinstance(frame, tuple)

    return f"""
<defs>
    <linearGradient id="bg_{badge_id}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="{bg[0]}" />
        <stop offset="55%" stop-color="{bg[1]}" />
        <stop offset="100%" stop-color="{bg[2]}" />
    </linearGradient>
    <linearGradient id="hull_{badge_id}" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="{hull_colors[0]}" />
        <stop offset="50%" stop-color="{hull_colors[1]}" />
        <stop offset="100%" stop-color="{hull_colors[2]}" />
    </linearGradient>
    <linearGradient id="frame_{badge_id}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="{frame[0]}" />
        <stop offset="50%" stop-color="{frame[1]}" />
        <stop offset="100%" stop-color="{frame[2]}" />
    </linearGradient>
    <filter id="shadow_{badge_id}" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="4" stdDeviation="0" flood-color="#000" flood-opacity="0.6"/>
    </filter>
    <filter id="glow_{badge_id}">
        <feGaussianBlur stdDeviation="1" result="blur"/>
        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="text_glow_{badge_id}" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="2" result="blur"/>
        <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>
    </filter>
    <clipPath id="clip_{badge_id}">
        <circle cx="256" cy="256" r="240" />
    </clipPath>
</defs>
""".strip()


def _get_ship_path(
    shape: ShipShape,
    badge_id: str,
    color: str,
    frame_index: int,
    upgrade_stage: int,
) -> str:
    hull_fill = f"url(#hull_{badge_id})"
    renderer = SHIP_RENDERERS.get(shape, SHIP_RENDERERS[ShipShape.SHUTTLE])
    return renderer.render(
        hull_fill=hull_fill,
        badge_id=badge_id,
        color=color,
        frame_index=frame_index,
        upgrade_stage=upgrade_stage,
    )


def _get_upgrade_overlay(badge_id: str, upgrade_stage: int) -> str:
    if upgrade_stage <= 0:
        return ""

    stages = min(upgrade_stage, 3)
    rings = []
    if stages >= 1:
        rings.append(
            f'<circle cx="256" cy="256" r="120" fill="none" '
            f'stroke="url(#frame_{badge_id})" stroke-width="3" opacity="0.35" '
            f'stroke-dasharray="6 8" />'
        )
    if stages >= 2:
        rings.append(
            f'<circle cx="256" cy="256" r="160" fill="none" '
            f'stroke="url(#frame_{badge_id})" stroke-width="2" opacity="0.25" '
            f'stroke-dasharray="2 10" />'
        )
    if stages >= 3:
        rings.append(
            f'<circle cx="256" cy="256" r="200" fill="none" '
            f'stroke="url(#frame_{badge_id})" stroke-width="2" opacity="0.2" '
            f'stroke-dasharray="1 6" />'
        )
    return f"""
<g filter="url(#glow_{badge_id})">
    {''.join(rings)}
</g>
""".strip()


def _get_grade_mark(badge_id: str, grade: str) -> str:
    """등급 마크를 원형 배지 안쪽(좌하단)에 배치."""
    from games.ship_system import parse_grade

    letter = parse_grade(grade).value
    colors = {
        "F": "#cfd8dc",
        "E": "#a5d6a7",
        "D": "#81d4fa",
        "C": "#ce93d8",
        "B": "#ffcc80",
        "A": "#ffd54f",
        "S": "#ff8a80",
    }
    fill = colors.get(letter, "#fff0f6")
    # 원 내부: 좌하단 (클립 원 r=240 기준 안전하게 inset)
    return f"""
<g shape-rendering="crispEdges" id="grade_{badge_id}">
  <rect x="86" y="348" width="64" height="48" fill="#3b1d2f" opacity="0.92"/>
  <rect x="90" y="352" width="56" height="40" fill="{fill}"/>
  <rect x="94" y="356" width="16" height="8" fill="#ffffff" opacity="0.35"/>
  <text x="118" y="382" font-family="Galmuri11, monospace" font-size="26" font-weight="bold"
        fill="#3b1d2f" text-anchor="middle">{letter}</text>
</g>
""".strip()


def _get_name_banner(badge_id: str, name: str, theme: dict[str, object]) -> str:
    """기체명을 상단 곡선 대신 가로 배너(고대비)로 배치."""
    label = (name or "SHIP")[:12]
    plate = theme["name_plate"]
    fill = theme["name_fill"]
    stroke = theme["name_stroke"]
    # 배지 안쪽 상단: 원 내부 y≈70–110
    return f"""
<g shape-rendering="crispEdges" id="name_{badge_id}">
  <rect x="118" y="72" width="276" height="44" fill="{plate}" opacity="0.94"/>
  <rect x="124" y="66" width="264" height="10" fill="{fill}" opacity="0.2"/>
  <rect x="124" y="78" width="264" height="32" fill="{plate}"/>
  <text x="256" y="101" font-family="Galmuri11, monospace" font-size="20" font-weight="bold"
        fill="{fill}" stroke="{stroke}" stroke-width="0.8" paint-order="stroke"
        text-anchor="middle" letter-spacing="1">{label}</text>
</g>
""".strip()


def _get_enhance_plate(badge_id: str, body_enhance: int, fallback_sub: str) -> str:
    """본체 +N 하단 플레이트. 강화 구간별 색/글로우 차별."""
    n = max(0, int(body_enhance))
    # sub 에 +숫자만 있으면 그 값 사용 (샘플/하위호환)
    if n == 0 and fallback_sub:
        stripped = fallback_sub.strip()
        if stripped.startswith("+"):
            try:
                n = max(0, int(stripped[1:]))
            except ValueError:
                pass
    style = enhance_text_style(n)
    label = f"+{n}"
    glow_attr = f' filter="url(#text_glow_{badge_id})"' if style["glow"] else ""
    stroke_w = int(style["stroke_w"])
    stroke_attr = (
        f' stroke="{style["stroke"]}" stroke-width="{stroke_w}" paint-order="stroke"'
        if stroke_w > 0
        else ""
    )
    font_size = int(style["font_size"])
    return f"""
<g shape-rendering="crispEdges" id="enhance_{badge_id}"{glow_attr}>
  <rect x="178" y="420" width="156" height="48" fill="{style["plate_edge"]}"/>
  <rect x="186" y="408" width="140" height="56" fill="{style["plate"]}"/>
  <rect x="198" y="400" width="116" height="12" fill="{style["plate_hi"]}"/>
  <text x="256" y="448" font-family="Galmuri11, monospace" font-size="{font_size}" font-weight="bold"
        fill="{style["text"]}"{stroke_attr} text-anchor="middle" letter-spacing="2">{label}</text>
</g>
""".strip()


def _generate_stars(rng: random.Random, count: int) -> str:
    stars: list[str] = []
    for _ in range(count):
        x = int(rng.random() * 480) + 16
        y = int(rng.random() * 360) + 40
        size = 4 if rng.random() < 0.7 else 6
        stars.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" />')
    return "\n".join(stars)


def _generate_pixel_clouds(badge_id: str) -> str:
    return f"""
<g fill="#ffc8dd">
    <rect x="70" y="116" width="44" height="16" />
    <rect x="86" y="100" width="54" height="16" />
    <rect x="376" y="146" width="48" height="16" />
    <rect x="352" y="162" width="72" height="16" />
</g>
<g fill="#cdb4db">
    <rect x="64" y="336" width="56" height="16" />
    <rect x="392" y="314" width="48" height="16" />
</g>
<g fill="url(#frame_{badge_id})" opacity="0.45">
    <rect x="142" y="74" width="8" height="8" />
    <rect x="362" y="92" width="8" height="8" />
    <rect x="118" y="270" width="8" height="8" />
</g>
""".strip()
