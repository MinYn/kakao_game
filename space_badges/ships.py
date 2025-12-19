from __future__ import annotations

from abc import ABC, abstractmethod


class ShipRenderer(ABC):
    @abstractmethod
    def render(self, hull_fill: str, badge_id: str, color: str) -> str:
        raise NotImplementedError


class ShuttleShip(ShipRenderer):
    def render(self, hull_fill: str, badge_id: str, color: str) -> str:
        tile_fill = "#222" if color == "black" else "#333"
        window_fill = "#112244"
        return f"""
<g transform="translate(0, -20)">
    <path d="M-30 -20 L-60 20 L-130 90 L-130 110 L-40 100 L-30 80 Z" fill="{hull_fill}" stroke="#999"
          stroke-width="1"/>
    <path d="M30 -20 L60 20 L130 90 L130 110 L40 100 L30 80 Z" fill="{hull_fill}" stroke="#999"
          stroke-width="1"/>
    <path d="M-35 -50 L-40 80 C-40 110 -20 125 0 125 C20 125 40 110 40 80 L35 -50 Z" fill="{hull_fill}" />
    <path d="M-35 -50 C-30 -100 -20 -140 0 -150 C20 -140 30 -100 35 -50 Z" fill="{hull_fill}" />
    <path d="M-15 -135 C-10 -145 0 -150 0 -150 C0 -150 10 -145 15 -135 L0 -125 Z" fill="{tile_fill}" />
    <path d="M-18 -10 L0 -15 L18 -10 L14 0 L-14 0 Z" fill="{window_fill}" stroke="#555" stroke-width="0.5"/>
    <path d="M0 40 L-2 100 L2 100 Z" fill="{hull_fill}" stroke="#ccc" />
    <path d="M-15 125 L-20 160 L-10 160 Z" fill="#0af" opacity="0.6">
        <animate attributeName="d"
                 values="M-15 125 L-20 160 L-10 160 Z;M-15 125 L-22 170 L-8 170 Z;M-15 125 L-20 160 L-10 160 Z"
                 dur="0.2s" repeatCount="indefinite"/>
    </path>
    <path d="M15 125 L10 160 L20 160 Z" fill="#0af" opacity="0.6">
        <animate attributeName="d"
                 values="M15 125 L10 160 L20 160 Z;M15 125 L8 170 L22 170 Z;M15 125 L10 160 L20 160 Z"
                 dur="0.2s" repeatCount="indefinite"/>
    </path>
</g>
""".strip()


class RocketShip(ShipRenderer):
    def render(self, hull_fill: str, badge_id: str, color: str) -> str:
        return f"""
<g transform="translate(0, -30)">
    <path d="M-25 100 L-60 160 L-25 150 Z" fill="{hull_fill}" stroke="#555"/>
    <path d="M25 100 L60 160 L25 150 Z" fill="{hull_fill}" stroke="#555"/>
    <rect x="-25" y="-50" width="50" height="200" fill="{hull_fill}" rx="2" />
    <rect x="-25" y="80" width="50" height="5" fill="#222" />
    <rect x="-25" y="10" width="50" height="5" fill="#222" />
    <path d="M-25 -50 L-15 -100 L0 -140 L15 -100 L25 -50 Z" fill="{hull_fill}" />
    <rect x="-2" y="-140" width="4" height="30" fill="#999" />
    <path d="M-15 150 L-20 180 L20 180 L15 150 Z" fill="#222" />
    <path d="M0 180 L-10 230 L10 230 Z" fill="#f50" opacity="0.8">
        <animate attributeName="d"
                 values="M0 180 L-10 230 L10 230 Z;M0 180 L-12 250 L12 250 Z;M0 180 L-10 230 L10 230 Z"
                 dur="0.1s" repeatCount="indefinite"/>
    </path>
</g>
""".strip()


class InterceptorShip(ShipRenderer):
    def render(self, hull_fill: str, badge_id: str, color: str) -> str:
        window_fill = "#112244"
        return f"""
<g transform="translate(0, 0)">
    <path d="M-20 -20 L-100 60 L-80 100 L-20 60 Z" fill="{hull_fill}" stroke="#555"/>
    <path d="M20 -20 L100 60 L80 100 L20 60 Z" fill="{hull_fill}" stroke="#555"/>
    <path d="M0 -120 L30 100 L0 120 L-30 100 Z" fill="{hull_fill}" />
    <path d="M0 -60 L10 -20 L0 0 L-10 -20 Z" fill="{window_fill}" />
    <circle cx="-30" cy="100" r="5" fill="#0ff" filter="url(#glow_{badge_id})"/>
    <circle cx="30" cy="100" r="5" fill="#0ff" filter="url(#glow_{badge_id})"/>
</g>
""".strip()


class LifterShip(ShipRenderer):
    def render(self, hull_fill: str, badge_id: str, color: str) -> str:
        return f"""
<g transform="translate(0, -10)">
    <rect x="-30" y="-80" width="60" height="180" rx="10" fill="#e76" />
    <rect x="-70" y="-20" width="30" height="140" rx="5" fill="#fff" />
    <path d="M-70 -20 L-55 -50 L-40 -20 Z" fill="#fff" />
    <rect x="40" y="-20" width="30" height="140" rx="5" fill="#fff" />
    <path d="M40 -20 L55 -50 L70 -20 Z" fill="#fff" />
    <path d="M0 -40 L20 20 L20 80 L0 90 L-20 80 L-20 20 Z" fill="{hull_fill}" stroke="#333" />
    <path d="M0 -40 L15 10 L0 0 L-15 10 Z" fill="#222" />
</g>
""".strip()
