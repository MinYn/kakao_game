from __future__ import annotations

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


def generate_svg(
    variant: BadgeVariant,
    index: int,
    star_seed: Optional[int] = None,
    upgrade_stage: int = 0,
) -> str:
    return _build_svg(
        variant,
        index,
        star_seed=star_seed,
        frame_index=0,
        upgrade_stage=upgrade_stage,
    )


def generate_svg_frames(
    variant: BadgeVariant,
    index: int,
    star_seed: Optional[int] = None,
    frame_count: int = 2,
    upgrade_stage: int = 0,
) -> list[str]:
    return [
        _build_svg(
            variant,
            index,
            star_seed=star_seed,
            frame_index=frame,
            upgrade_stage=upgrade_stage,
        )
        for frame in range(frame_count)
    ]


def _build_svg(
    variant: BadgeVariant,
    index: int,
    star_seed: Optional[int],
    frame_index: int,
    upgrade_stage: int,
) -> str:
    badge_id = f"badge_{index}"
    defs = _get_defs(badge_id, variant.color)
    ship_path = _get_ship_path(
        variant.shape,
        badge_id,
        variant.color,
        frame_index,
        upgrade_stage,
    )
    star_random = random.Random(star_seed)
    upgrade_overlay = _get_upgrade_overlay(badge_id, upgrade_stage)

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
        <path d="M-100 438 Q256 {'462' if variant.shape == ShipShape.ROCKET else '374'} 612 438 V512 H-100 Z"
              fill="{_get_atmosphere_color(variant.color)}" fill-opacity="0.32" />
    </g>

    <g transform="translate(256, 256) scale({'0.9' if variant.shape == ShipShape.ROCKET else '1.1'})"
       filter="url(#shadow_{badge_id})">
        {ship_path}
    </g>

    {upgrade_overlay}

    <g shape-rendering="crispEdges">
        <circle cx="256" cy="256" r="238" fill="none" stroke="#ff8fab" stroke-width="12" />
        <circle cx="256" cy="256" r="226" fill="none" stroke="#fff0f6" stroke-width="10" />
        <circle cx="256" cy="256" r="214" fill="none" stroke="#ff5d8f"
                stroke-width="8" stroke-dasharray="12 10" />
        <path d="M256 24 V48 M488 256 H464 M256 488 V464 M24 256 H48"
              stroke="#3b1d2f" stroke-width="8" opacity="0.45" />

        <path d="M144 78 A 190 190 0 0 1 368 78" id="curve_{badge_id}" fill="none" />
        <text font-family="Galmuri11, monospace" font-size="18" font-weight="bold"
              fill="#ff5d8f" stroke="#3b1d2f" stroke-width="1" paint-order="stroke"
              letter-spacing="2" text-anchor="middle">
            <textPath href="#curve_{badge_id}" startOffset="50%">{variant.name}</textPath>
        </text>

        <rect x="178" y="426" width="156" height="42" fill="#3b1d2f" />
        <rect x="190" y="414" width="132" height="54" fill="#ffd166" />
        <rect x="206" y="406" width="100" height="8" fill="#fff3b0" />
        <text x="256" y="451" font-family="Galmuri11, monospace" font-size="16" font-weight="bold"
              fill="#3b1d2f" text-anchor="middle" letter-spacing="2">{variant.sub}</text>
    </g>
</svg>
""".strip()


def _get_defs(badge_id: str, color: str) -> str:
    hull_colors = {
        "white": ["#e0e0e0", "#ffffff", "#d0d0d0"],
        "silver": ["#7a7f8e", "#a0a5b0", "#606570"],
        "dark": ["#2a2a35", "#3a3a45", "#1a1a25"],
        "black": ["#1a1a1a", "#333333", "#000000"],
        "gold": ["#d4af37", "#fcf6ba", "#aa8822"],
        "blue": ["#112244", "#224488", "#001133"],
        "orange": ["#cc5500", "#ff7722", "#aa4400"],
    }.get(color, ["#e0e0e0", "#ffffff", "#d0d0d0"])

    return f"""
<defs>
    <linearGradient id="bg_{badge_id}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#6d5dfc" />
        <stop offset="55%" stop-color="#9b5de5" />
        <stop offset="100%" stop-color="#f15bb5" />
    </linearGradient>
    <linearGradient id="hull_{badge_id}" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="{hull_colors[0]}" />
        <stop offset="50%" stop-color="{hull_colors[1]}" />
        <stop offset="100%" stop-color="{hull_colors[2]}" />
    </linearGradient>
    <linearGradient id="frame_{badge_id}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ff8fab" />
        <stop offset="50%" stop-color="#ffd166" />
        <stop offset="100%" stop-color="#80ed99" />
    </linearGradient>
    <filter id="shadow_{badge_id}" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="4" stdDeviation="0" flood-color="#000" flood-opacity="0.6"/>
    </filter>
    <filter id="glow_{badge_id}">
        <feGaussianBlur stdDeviation="1" result="blur"/>
        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
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


def _get_atmosphere_color(color: str) -> str:
    if color == "orange":
        return "#ffb703"
    if color == "gold":
        return "#ffe066"
    if color in {"blue", "dark", "black"}:
        return "#80ed99"
    return "#8ecae6"
