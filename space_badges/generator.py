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

# shape 별 기본 배경/프레임/대기 팔레트 (딥 스페이스 + 메탈 림)
_SHAPE_THEMES: dict[ShipShape, dict[str, object]] = {
    ShipShape.SHUTTLE: {
        "bg": ("#1e3a8a", "#5b21b6", "#9d174d"),
        "bg_hi": "#93c5fd",
        "frame": ("#93c5fd", "#f9a8d4", "#fde68a"),
        "ring": "#7dd3fc",
        "ring_mid": "#e0f2fe",
        "ring_outer": "#1e3a5f",
        "ring_dash": "#38bdf8",
        "atmosphere": "#67e8f9",
        "planet": "#6366f1",
        "name_plate": "#0f2744",
        "name_fill": "#f0f9ff",
        "name_stroke": "#020617",
        "name_accent": "#38bdf8",
    },
    ShipShape.ROCKET: {
        "bg": ("#7c2d12", "#b91c1c", "#431407"),
        "bg_hi": "#fdba74",
        "frame": ("#fdba74", "#fde047", "#fca5a5"),
        "ring": "#fb923c",
        "ring_mid": "#ffedd5",
        "ring_outer": "#7c2d12",
        "ring_dash": "#f97316",
        "atmosphere": "#fbbf24",
        "planet": "#ea580c",
        "name_plate": "#431407",
        "name_fill": "#fff7ed",
        "name_stroke": "#1c0a00",
        "name_accent": "#fb923c",
    },
    ShipShape.INTERCEPTOR: {
        "bg": ("#1e1b4b", "#4c1d95", "#0f172a"),
        "bg_hi": "#a5b4fc",
        "frame": ("#a5b4fc", "#c4b5fd", "#e9d5ff"),
        "ring": "#a78bfa",
        "ring_mid": "#ede9fe",
        "ring_outer": "#1e1b4b",
        "ring_dash": "#8b5cf6",
        "atmosphere": "#c4b5fd",
        "planet": "#7c3aed",
        "name_plate": "#0f0a2a",
        "name_fill": "#f5f3ff",
        "name_stroke": "#02010a",
        "name_accent": "#a78bfa",
    },
    ShipShape.LIFTER: {
        "bg": ("#134e4a", "#854d0e", "#7c2d12"),
        "bg_hi": "#5eead4",
        "frame": ("#5eead4", "#fde047", "#fdba74"),
        "ring": "#2dd4bf",
        "ring_mid": "#ccfbf1",
        "ring_outer": "#115e59",
        "ring_dash": "#14b8a6",
        "atmosphere": "#fbbf24",
        "planet": "#0d9488",
        "name_plate": "#042f2e",
        "name_fill": "#f0fdfa",
        "name_stroke": "#010f0e",
        "name_accent": "#2dd4bf",
    },
}

# color 키로 배경/프레임 틴트 보정 (기체별 색 다양성)
# 테스트·기존 팔레트 키 유지: white 에 #7dd3fc, gold 에 #fbbf24
_COLOR_BG_OVERRIDES: dict[str, tuple[str, str, str]] = {
    "white": ("#0c4a6e", "#5b21b6", "#9d174d"),
    "silver": ("#334155", "#475569", "#1e293b"),
    "dark": ("#1e1b4b", "#0f172a", "#020617"),
    "black": ("#111827", "#030712", "#000000"),
    "gold": ("#78350f", "#b45309", "#451a03"),
    "blue": ("#1e3a8a", "#1d4ed8", "#0f172a"),
    "orange": ("#9a3412", "#c2410c", "#431407"),
}

# 밝은 틴트 포인트 (그라데이션 하이라이트 + 테스트 호환 스와치)
_COLOR_BG_HI: dict[str, str] = {
    "white": "#7dd3fc",
    "silver": "#cbd5e1",
    "dark": "#818cf8",
    "black": "#fbbf24",
    "gold": "#fbbf24",
    "blue": "#60a5fa",
    "orange": "#fb923c",
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
# 시인성 우선: 큰 폰트 + 항상 두꺼운 외곽선(흑) + 밝은 페이스 + 어두운 텍스트
_ENHANCE_TEXT_STYLES: tuple[dict[str, object], ...] = (
    {  # 0–4
        "min": 0,
        "plate": "#e2e8f0",
        "plate_hi": "#f8fafc",
        "plate_edge": "#0f172a",
        "text": "#020617",
        "stroke": "#ffffff",
        "stroke_w": 3,
        "glow": False,
        "font_size": 30,
    },
    {  # 5–14
        "min": 5,
        "plate": "#67e8f9",
        "plate_hi": "#ecfeff",
        "plate_edge": "#083344",
        "text": "#042f2e",
        "stroke": "#ffffff",
        "stroke_w": 3,
        "glow": False,
        "font_size": 32,
    },
    {  # 15–29
        "min": 15,
        "plate": "#fde047",
        "plate_hi": "#fefce8",
        "plate_edge": "#422006",
        "text": "#1c1917",
        "stroke": "#ffffff",
        "stroke_w": 3,
        "glow": True,
        "font_size": 34,
    },
    {  # 30+
        "min": 30,
        "plate": "#f9a8d4",
        "plate_hi": "#fdf2f8",
        "plate_edge": "#500724",
        "text": "#1f0510",
        "stroke": "#ffffff",
        "stroke_w": 4,
        "glow": True,
        "font_size": 36,
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
    if variant.color in _COLOR_BG_HI:
        base["bg_hi"] = _COLOR_BG_HI[variant.color]
    if variant.color in _COLOR_FRAME_OVERRIDES:
        base["frame"] = _COLOR_FRAME_OVERRIDES[variant.color]
    if variant.color in {"dark", "black"}:
        base["name_plate"] = "#050814"
        base["name_fill"] = "#f8fafc"
        base["name_accent"] = "#fbbf24" if variant.color == "black" else "#a5b4fc"
    if variant.color == "gold":
        base["name_plate"] = "#451a03"
        base["name_fill"] = "#fffbeb"
        base["name_accent"] = "#fbbf24"
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
    upgrade_overlay = _get_upgrade_overlay(badge_id, upgrade_stage, theme)
    grade_mark = _get_grade_mark(badge_id, grade)
    name_banner = _get_name_banner(badge_id, variant.name, theme)
    enhance_plate = _get_enhance_plate(badge_id, body_enhance, variant.sub)
    frame = _get_badge_frame(badge_id, theme)
    scene = _get_space_scene(badge_id, theme, star_random, upgrade_stage, variant.shape)

    # rocket is longer horizontally — slight scale down so rim clearance stays even
    ship_scale = "0.88" if variant.shape == ShipShape.ROCKET else "1.05"
    ship_y = 258 if variant.shape == ShipShape.LIFTER else 252

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="w-full h-full" shape-rendering="crispEdges">
    {defs}

    <g clip-path="url(#clip_{badge_id})">
        {scene}
    </g>

    <g transform="translate(256, {ship_y}) scale({ship_scale})"
       filter="url(#shadow_{badge_id})">
        {ship_path}
    </g>

    {upgrade_overlay}
    {frame}
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
    bg_hi = theme.get("bg_hi", "#93c5fd")
    assert isinstance(bg, tuple) and isinstance(frame, tuple)

    return f"""
<defs>
    <radialGradient id="bg_{badge_id}" cx="38%" cy="32%" r="78%">
        <stop offset="0%" stop-color="{bg_hi}" stop-opacity="0.55" />
        <stop offset="35%" stop-color="{bg[0]}" />
        <stop offset="72%" stop-color="{bg[1]}" />
        <stop offset="100%" stop-color="{bg[2]}" />
    </radialGradient>
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
    <linearGradient id="rim_{badge_id}" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="{frame[0]}" />
        <stop offset="45%" stop-color="{frame[1]}" />
        <stop offset="100%" stop-color="{theme["ring_outer"]}" />
    </linearGradient>
    <radialGradient id="vignette_{badge_id}" cx="50%" cy="48%" r="55%">
        <stop offset="55%" stop-color="#000000" stop-opacity="0" />
        <stop offset="100%" stop-color="#000000" stop-opacity="0.42" />
    </radialGradient>
    <filter id="shadow_{badge_id}" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="6" stdDeviation="0" flood-color="#000" flood-opacity="0.55"/>
    </filter>
    <filter id="glow_{badge_id}">
        <feGaussianBlur stdDeviation="1.2" result="blur"/>
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
        <circle cx="256" cy="256" r="236" />
    </clipPath>
</defs>
""".strip()


def _get_space_scene(
    badge_id: str,
    theme: dict[str, object],
    star_random: random.Random,
    upgrade_stage: int,
    shape: ShipShape,
) -> str:
    """Deep-space plate: radial sky, stars, nebula, planet limb, vignette."""
    planet = theme["planet"]
    atmosphere = theme["atmosphere"]
    # planet position varies slightly by shape so catalog variety reads clearer
    planet_cx = {
        ShipShape.SHUTTLE: 380,
        ShipShape.ROCKET: 120,
        ShipShape.INTERCEPTOR: 360,
        ShipShape.LIFTER: 140,
    }.get(shape, 360)
    planet_cy = 400 if shape != ShipShape.ROCKET else 390
    planet_r = 96 if shape == ShipShape.LIFTER else 88

    return f"""
        <rect width="512" height="512" fill="url(#bg_{badge_id})" />
        <g fill="#ffffff" shape-rendering="crispEdges">
            {_generate_stars(star_random, 18 + max(upgrade_stage, 0) * 3)}
        </g>
        <g opacity="0.5" shape-rendering="crispEdges">
            {_generate_pixel_clouds(badge_id, theme)}
        </g>
        <!-- distant planet limb -->
        <circle cx="{planet_cx}" cy="{planet_cy}" r="{planet_r}"
                fill="{planet}" fill-opacity="0.35" />
        <circle cx="{planet_cx - 18}" cy="{planet_cy - 14}" r="{max(24, planet_r // 3)}"
                fill="{atmosphere}" fill-opacity="0.18" />
        <path d="M-40 420 Q256 360 552 420 V520 H-40 Z"
              fill="{atmosphere}" fill-opacity="0.16" />
        <rect width="512" height="512" fill="url(#vignette_{badge_id})" />
""".strip()


def _get_badge_frame(badge_id: str, theme: dict[str, object]) -> str:
    """Pixel medal rim: outer dark band, metallic ring, tick marks, studs."""
    ring = theme["ring"]
    ring_mid = theme["ring_mid"]
    ring_dash = theme["ring_dash"]
    ring_outer = theme["ring_outer"]
    accent = theme.get("name_accent", ring)

    # compass studs (pixel blocks)
    studs = []
    for cx, cy in ((256, 28), (484, 256), (256, 484), (28, 256)):
        studs.append(f'<rect x="{cx - 10}" y="{cy - 10}" width="20" height="20" fill="{ring_outer}"/>')
        studs.append(f'<rect x="{cx - 6}" y="{cy - 6}" width="12" height="12" fill="{ring_mid}"/>')
        studs.append(f'<rect x="{cx - 2}" y="{cy - 2}" width="4" height="4" fill="{accent}"/>')

    # diagonal micro-studs
    for cx, cy in ((86, 86), (426, 86), (86, 426), (426, 426)):
        studs.append(f'<rect x="{cx - 4}" y="{cy - 4}" width="8" height="8" fill="{ring}" opacity="0.85"/>')

    return f"""
<g shape-rendering="crispEdges" id="frame_{badge_id}_chrome">
  <!-- outer dark bevel -->
  <circle cx="256" cy="256" r="248" fill="none" stroke="{ring_outer}" stroke-width="16" />
  <circle cx="256" cy="256" r="248" fill="none" stroke="#050505" stroke-width="4" opacity="0.55" />
  <!-- metallic rim -->
  <circle cx="256" cy="256" r="236" fill="none" stroke="url(#rim_{badge_id})" stroke-width="14" />
  <circle cx="256" cy="256" r="226" fill="none" stroke="{ring_mid}" stroke-width="5" opacity="0.9" />
  <!-- inner track + dashed orbit -->
  <circle cx="256" cy="256" r="216" fill="none" stroke="{ring}" stroke-width="3" opacity="0.55" />
  <circle cx="256" cy="256" r="210" fill="none" stroke="{ring_dash}"
          stroke-width="6" stroke-dasharray="10 14" opacity="0.95" />
  <!-- pixel tick notches on cardinals (inner) -->
  <rect x="250" y="42" width="12" height="16" fill="{ring_mid}" />
  <rect x="250" y="454" width="12" height="16" fill="{ring_mid}" />
  <rect x="42" y="250" width="16" height="12" fill="{ring_mid}" />
  <rect x="454" y="250" width="16" height="12" fill="{ring_mid}" />
  {"".join(studs)}
</g>
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


def _get_upgrade_overlay(badge_id: str, upgrade_stage: int, theme: dict[str, object]) -> str:
    if upgrade_stage <= 0:
        return ""

    stages = min(upgrade_stage, 3)
    accent = theme.get("name_accent", "#40e0d0")
    rings = []
    if stages >= 1:
        rings.append(
            f'<circle cx="256" cy="256" r="128" fill="none" '
            f'stroke="{accent}" stroke-width="3" opacity="0.4" '
            f'stroke-dasharray="8 10" />'
        )
    if stages >= 2:
        rings.append(
            f'<circle cx="256" cy="256" r="158" fill="none" '
            f'stroke="url(#frame_{badge_id})" stroke-width="3" opacity="0.35" '
            f'stroke-dasharray="4 12" />'
        )
        # pixel orbit nodes
        for x, y in ((256, 98), (414, 256), (256, 414), (98, 256)):
            rings.append(
                f'<rect x="{x - 4}" y="{y - 4}" width="8" height="8" fill="{accent}" opacity="0.75"/>'
            )
    if stages >= 3:
        rings.append(
            f'<circle cx="256" cy="256" r="188" fill="none" '
            f'stroke="#ffd54f" stroke-width="2" opacity="0.45" '
            f'stroke-dasharray="2 8" />'
        )
        for x, y in ((180, 120), (332, 120), (180, 392), (332, 392)):
            rings.append(
                f'<rect x="{x - 3}" y="{y - 3}" width="6" height="6" fill="#ffd54f" opacity="0.85"/>'
            )
    return f"""
<g filter="url(#glow_{badge_id})" id="upgrade_{badge_id}">
    {''.join(rings)}
</g>
""".strip()


def _get_grade_mark(badge_id: str, grade: str) -> str:
    """등급 젬 — 배지 안쪽 좌하단, 픽셀 방패 프레임."""
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
    # inset from rim (~x80–150, y340–410) — not outer corner origin
    return f"""
<g shape-rendering="crispEdges" id="grade_{badge_id}">
  <!-- outer shield shadow -->
  <rect x="78" y="352" width="72" height="56" fill="#050505" opacity="0.55"/>
  <rect x="74" y="348" width="72" height="56" fill="#1a1020"/>
  <!-- top gem cut -->
  <rect x="86" y="340" width="48" height="12" fill="#1a1020"/>
  <rect x="94" y="336" width="32" height="8" fill="#1a1020"/>
  <!-- face -->
  <rect x="82" y="352" width="56" height="44" fill="{fill}"/>
  <rect x="90" y="344" width="40" height="12" fill="{fill}"/>
  <rect x="98" y="340" width="24" height="8" fill="{fill}"/>
  <!-- shine -->
  <rect x="86" y="356" width="16" height="8" fill="#ffffff" opacity="0.4"/>
  <rect x="90" y="348" width="12" height="6" fill="#ffffff" opacity="0.25"/>
  <!-- bottom lip -->
  <rect x="82" y="388" width="56" height="6" fill="#050505" opacity="0.2"/>
  <text x="110" y="384" font-family="Galmuri11, monospace" font-size="28" font-weight="bold"
        fill="#1a1020" text-anchor="middle">{letter}</text>
</g>
""".strip()


def _get_name_banner(badge_id: str, name: str, theme: dict[str, object]) -> str:
    """상단 HUD 네임 플레이트 — 양옆 픽셀 캡 + 악센트 바."""
    label = (name or "SHIP")[:12]
    plate = theme["name_plate"]
    fill = theme["name_fill"]
    stroke = theme["name_stroke"]
    accent = theme.get("name_accent", theme["ring"])
    return f"""
<g shape-rendering="crispEdges" id="name_{badge_id}">
  <!-- side wing caps -->
  <rect x="96" y="78" width="20" height="36" fill="{plate}"/>
  <rect x="396" y="78" width="20" height="36" fill="{plate}"/>
  <rect x="88" y="86" width="16" height="20" fill="{accent}" opacity="0.85"/>
  <rect x="408" y="86" width="16" height="20" fill="{accent}" opacity="0.85"/>
  <!-- main plate -->
  <rect x="112" y="70" width="288" height="52" fill="#050505" opacity="0.35"/>
  <rect x="116" y="66" width="280" height="52" fill="{plate}"/>
  <rect x="124" y="74" width="264" height="36" fill="{plate}"/>
  <!-- top accent strip -->
  <rect x="124" y="66" width="264" height="8" fill="{accent}"/>
  <rect x="132" y="66" width="40" height="8" fill="#ffffff" opacity="0.35"/>
  <!-- bottom rail -->
  <rect x="124" y="110" width="264" height="4" fill="{accent}" opacity="0.55"/>
  <text x="256" y="100" font-family="Galmuri11, monospace" font-size="20" font-weight="bold"
        fill="{fill}" stroke="{stroke}" stroke-width="0.9" paint-order="stroke"
        text-anchor="middle" letter-spacing="1.5">{label}</text>
</g>
""".strip()


def _get_enhance_plate(badge_id: str, body_enhance: int, fallback_sub: str) -> str:
    """본체 +N 하단 HUD 칩 — 큰 숫자·고대비·두꺼운 외곽선으로 썸네일 시인성 확보."""
    n = max(0, int(body_enhance))
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
    font_size = int(style["font_size"])
    # 이중 외곽: 바깥 검정 할로 + 안쪽 흰색 스트로크로 배경과 분리
    return f"""
<g shape-rendering="crispEdges" id="enhance_{badge_id}"{glow_attr}>
  <!-- outer black frame (rim separation) -->
  <rect x="148" y="392" width="216" height="76" fill="#050505" opacity="0.55"/>
  <rect x="152" y="388" width="208" height="76" fill="#050505"/>
  <!-- side bolts -->
  <rect x="152" y="408" width="18" height="36" fill="{style["plate_edge"]}"/>
  <rect x="342" y="408" width="18" height="36" fill="{style["plate_edge"]}"/>
  <rect x="156" y="416" width="10" height="20" fill="{style["plate_hi"]}"/>
  <rect x="346" y="416" width="10" height="20" fill="{style["plate_hi"]}"/>
  <!-- chassis -->
  <rect x="168" y="396" width="176" height="60" fill="{style["plate_edge"]}"/>
  <rect x="176" y="388" width="160" height="64" fill="{style["plate"]}"/>
  <!-- top bevel / light bar -->
  <rect x="184" y="380" width="144" height="16" fill="{style["plate_hi"]}"/>
  <rect x="196" y="380" width="48" height="8" fill="#ffffff" opacity="0.55"/>
  <!-- inner number well (darker inset for contrast) -->
  <rect x="188" y="404" width="136" height="40" fill="#050505" opacity="0.12"/>
  <!-- bottom lip -->
  <rect x="176" y="444" width="160" height="8" fill="{style["plate_edge"]}"/>
  <!-- number: black outline underlay then white stroke + dark fill -->
  <text x="256" y="436" font-family="Galmuri11, monospace" font-size="{font_size}" font-weight="bold"
        fill="none" stroke="#050505" stroke-width="{stroke_w + 3}" paint-order="stroke"
        text-anchor="middle" letter-spacing="1">{label}</text>
  <text x="256" y="436" font-family="Galmuri11, monospace" font-size="{font_size}" font-weight="bold"
        fill="{style["text"]}" stroke="{style["stroke"]}" stroke-width="{stroke_w}" paint-order="stroke"
        text-anchor="middle" letter-spacing="1">{label}</text>
</g>
""".strip()


def _generate_stars(rng: random.Random, count: int) -> str:
    stars: list[str] = []
    for _ in range(count):
        x = int(rng.random() * 460) + 26
        y = int(rng.random() * 400) + 36
        kind = rng.random()
        if kind < 0.55:
            size = 3 if rng.random() < 0.5 else 4
            stars.append(
                f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill-opacity="0.95"/>'
            )
        elif kind < 0.8:
            # plus sparkle
            stars.append(f'<rect x="{x}" y="{y + 3}" width="10" height="3" fill-opacity="0.9"/>')
            stars.append(f'<rect x="{x + 3}" y="{y}" width="3" height="10" fill-opacity="0.9"/>')
        else:
            # diamond-ish 2-step
            stars.append(f'<rect x="{x + 4}" y="{y}" width="4" height="4" fill-opacity="0.85"/>')
            stars.append(f'<rect x="{x}" y="{y + 4}" width="12" height="4" fill-opacity="0.85"/>')
            stars.append(f'<rect x="{x + 4}" y="{y + 8}" width="4" height="4" fill-opacity="0.85"/>')
    return "\n".join(stars)


def _generate_pixel_clouds(badge_id: str, theme: dict[str, object]) -> str:
    """Sparse nebula blobs tinted by frame gradient + soft pastel banks."""
    accent = theme.get("name_accent", "#c4b5fd")
    return f"""
<g fill="#f9a8d4">
    <rect x="56" y="100" width="36" height="10" />
    <rect x="72" y="90" width="44" height="10" />
    <rect x="88" y="110" width="22" height="10" />
    <rect x="360" y="128" width="40" height="10" />
    <rect x="344" y="140" width="56" height="10" />
    <rect x="380" y="118" width="18" height="10" />
</g>
<g fill="{accent}" opacity="0.7">
    <rect x="48" y="320" width="40" height="10" />
    <rect x="64" y="332" width="28" height="10" />
    <rect x="376" y="292" width="40" height="10" />
    <rect x="392" y="304" width="24" height="10" />
</g>
<g fill="url(#frame_{badge_id})" opacity="0.45">
    <rect x="150" y="64" width="8" height="8" />
    <rect x="348" y="84" width="8" height="8" />
    <rect x="120" y="250" width="8" height="8" />
    <rect x="300" y="230" width="8" height="8" />
    <rect x="200" y="300" width="6" height="6" />
</g>
""".strip()
