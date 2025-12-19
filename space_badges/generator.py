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


def generate_svg(variant: BadgeVariant, index: int, star_seed: Optional[int] = None) -> str:
    badge_id = f"badge_{index}"
    defs = _get_defs(badge_id, variant.color)
    ship_path = _get_ship_path(variant.shape, badge_id, variant.color)
    star_random = random.Random(star_seed)

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="w-full h-full">
    {defs}

    <g clip-path="url(#clip_{badge_id})">
        <rect width="512" height="512" fill="url(#bg_{badge_id})" />
        <g fill="#FFF" fill-opacity="0.8">
            {_generate_stars(star_random, 10)}
        </g>
        <path d="M-100 450 Q256 {'480' if variant.shape == ShipShape.ROCKET else '350'} 612 450 V512 H-100 Z"
              fill="{_get_atmosphere_color(variant.color)}" fill-opacity="0.2"
              filter="url(#glow_{badge_id})" />
    </g>

    <g transform="translate(256, 256) scale({'0.9' if variant.shape == ShipShape.ROCKET else '1.1'})"
       filter="url(#shadow_{badge_id})">
        {ship_path}
    </g>

    <g>
        <circle cx="256" cy="256" r="230" fill="none" stroke="url(#frame_{badge_id})" stroke-width="8" />
        <path d="M256 26 V46 M476 256 H456 M256 486 V466 M36 256 H56"
              stroke="#000" stroke-width="4" opacity="0.5" />

        <path d="M156 80 A 180 180 0 0 1 356 80" id="curve_{badge_id}" fill="none" />
        <text font-family="sans-serif" font-size="14" font-weight="bold" fill="url(#frame_{badge_id})"
              letter-spacing="2" text-anchor="middle">
            <textPath href="#curve_{badge_id}" startOffset="50%">{variant.name}</textPath>
        </text>

        <path d="M196 460 L216 430 H296 L316 460 H196 Z"
              fill="url(#frame_{badge_id})" filter="url(#shadow_{badge_id})" />
        <text x="256" y="452" font-family="sans-serif" font-size="14" font-weight="bold"
              fill="#3e2b00" text-anchor="middle" letter-spacing="1">{variant.sub}</text>
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
        <stop offset="0%" stop-color="#050510" />
        <stop offset="100%" stop-color="#101020" />
    </linearGradient>
    <linearGradient id="hull_{badge_id}" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="{hull_colors[0]}" />
        <stop offset="50%" stop-color="{hull_colors[1]}" />
        <stop offset="100%" stop-color="{hull_colors[2]}" />
    </linearGradient>
    <linearGradient id="frame_{badge_id}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#bf953f" />
        <stop offset="50%" stop-color="#fcf6ba" />
        <stop offset="100%" stop-color="#aa771c" />
    </linearGradient>
    <filter id="shadow_{badge_id}" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.6"/>
    </filter>
    <filter id="glow_{badge_id}">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <clipPath id="clip_{badge_id}">
        <circle cx="256" cy="256" r="240" />
    </clipPath>
</defs>
""".strip()


def _get_ship_path(shape: ShipShape, badge_id: str, color: str) -> str:
    hull_fill = f"url(#hull_{badge_id})"
    renderer = SHIP_RENDERERS.get(shape, SHIP_RENDERERS[ShipShape.SHUTTLE])
    return renderer.render(hull_fill=hull_fill, badge_id=badge_id, color=color)


def _generate_stars(rng: random.Random, count: int) -> str:
    stars: list[str] = []
    for _ in range(count):
        cx = rng.random() * 512
        cy = rng.random() * 512
        radius = rng.random() * 1.5 + 0.5
        stars.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" />')
    return "\n".join(stars)


def _get_atmosphere_color(color: str) -> str:
    if color == "orange":
        return "#ff4400"
    if color == "gold":
        return "#ffd700"
    return "#0066ff"
