from __future__ import annotations

from abc import ABC, abstractmethod


class ShipRenderer(ABC):
    @abstractmethod
    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        raise NotImplementedError


class ShuttleShip(ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.append(
                f"""
    <rect x="-5" y="-185" width="10" height="30" fill="#7ef" opacity="0.9" />
    <circle cx="0" cy="-192" r="10" fill="#3ff" filter="url(#glow_{badge_id})"/>
    <circle cx="0" cy="-192" r="16" fill="none" stroke="#6ff" stroke-width="2" opacity="0.6" />
    """.strip()
            )
        if upgrade_stage >= 2:
            parts.append(
                """
    <path d="M-90 20 L-140 80 L-100 100 Z" fill="#2dd" stroke="#9ff" stroke-width="1.2" opacity="0.8"/>
    <path d="M90 20 L140 80 L100 100 Z" fill="#2dd" stroke="#9ff" stroke-width="1.2" opacity="0.8"/>
    <rect x="-120" y="100" width="240" height="12" rx="6" fill="#1bf" opacity="0.5"/>
    """.strip()
            )
        if upgrade_stage >= 3:
            parts.append(
                '<rect x="-70" y="40" width="30" height="80" rx="6" fill="#ffd54f" opacity="0.85" />'
            )
            parts.append(
                '<rect x="40" y="40" width="30" height="80" rx="6" fill="#ffd54f" opacity="0.85" />'
            )
            parts.append(
                f'<circle cx="0" cy="20" r="30" fill="#fff3b0" opacity="0.35" filter="url(#glow_{badge_id})" />'
            )
        return parts

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        tile_fill = "#222" if color == "black" else "#333"
        window_fill = "#112244"
        upgrade_parts = self._upgrade_parts(badge_id, upgrade_stage)
        flame_frames = [
            ("M-15 125 L-20 160 L-10 160 Z", "M15 125 L10 160 L20 160 Z"),
            ("M-15 125 L-22 170 L-8 170 Z", "M15 125 L8 170 L22 170 Z"),
        ]
        flame_left, flame_right = flame_frames[frame_index % len(flame_frames)]
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
    {''.join(upgrade_parts)}
    <path d="{flame_left}" fill="#0af" opacity="0.6" />
    <path d="{flame_right}" fill="#0af" opacity="0.6" />
</g>
""".strip()


class RocketShip(ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.append(
                """
    <path d="M-45 110 L-80 190 L-30 180 Z" fill="#7cf" stroke="#cff" stroke-width="1.2" opacity="0.8"/>
    <path d="M45 110 L80 190 L30 180 Z" fill="#7cf" stroke="#cff" stroke-width="1.2" opacity="0.8"/>
    <rect x="-60" y="185" width="120" height="10" rx="5" fill="#4ef" opacity="0.5"/>
    """.strip()
            )
        if upgrade_stage >= 2:
            parts.append(
                f"""
    <ellipse cx="0" cy="30" rx="55" ry="14" fill="none" stroke="#aef"
             stroke-width="3" filter="url(#glow_{badge_id})"/>
    <ellipse cx="0" cy="30" rx="40" ry="10" fill="none" stroke="#5ff"
             stroke-width="2" opacity="0.7"/>
    """.strip()
            )
        if upgrade_stage >= 3:
            parts.append(
                f'<circle cx="0" cy="40" r="30" fill="#ffd54f" opacity="0.6" '
                f'filter="url(#glow_{badge_id})" />'
            )
            parts.append(
                '<path d="M-25 -120 L0 -170 L25 -120 Z" fill="#ffe082" opacity="0.8" />'
            )
        return parts

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        flame_frames = [
            "M0 180 L-10 230 L10 230 Z",
            "M0 180 L-12 250 L12 250 Z",
        ]
        flame_path = flame_frames[frame_index % len(flame_frames)]
        upgrade_parts = self._upgrade_parts(badge_id, upgrade_stage)
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
    {''.join(upgrade_parts)}
    <path d="{flame_path}" fill="#f50" opacity="0.8" />
</g>
""".strip()


class InterceptorShip(ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.append(
                """
    <path d="M-70 -5 L-150 70 L-120 110 L-40 50 Z" fill="#7af" stroke="#cfe" stroke-width="1.2" opacity="0.85"/>
    <path d="M70 -5 L150 70 L120 110 L40 50 Z" fill="#7af" stroke="#cfe" stroke-width="1.2" opacity="0.85"/>
    """.strip()
            )
        if upgrade_stage >= 2:
            parts.append(
                f"""
    <circle cx="0" cy="-130" r="18" fill="#0ff" opacity="0.75" filter="url(#glow_{badge_id})"/>
    <circle cx="0" cy="-130" r="28" fill="none" stroke="#7ff" stroke-width="2" opacity="0.6" />
    """.strip()
            )
        if upgrade_stage >= 3:
            parts.append(
                f'<circle cx="0" cy="-20" r="26" fill="#7bf" opacity="0.55" '
                f'filter="url(#glow_{badge_id})" />'
            )
            parts.append(
                '<rect x="-90" y="90" width="180" height="14" rx="7" fill="#4ff" opacity="0.5" />'
            )
        return parts

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        window_fill = "#112244"
        upgrade_parts = self._upgrade_parts(badge_id, upgrade_stage)
        return f"""
<g transform="translate(0, 0)">
    <path d="M-20 -20 L-100 60 L-80 100 L-20 60 Z" fill="{hull_fill}" stroke="#555"/>
    <path d="M20 -20 L100 60 L80 100 L20 60 Z" fill="{hull_fill}" stroke="#555"/>
    <path d="M0 -120 L30 100 L0 120 L-30 100 Z" fill="{hull_fill}" />
    <path d="M0 -60 L10 -20 L0 0 L-10 -20 Z" fill="{window_fill}" />
    {''.join(upgrade_parts)}
    <circle cx="-30" cy="100" r="5" fill="#0ff" filter="url(#glow_{badge_id})"/>
    <circle cx="30" cy="100" r="5" fill="#0ff" filter="url(#glow_{badge_id})"/>
</g>
""".strip()


class LifterShip(ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.append(
                """
    <rect x="-30" y="-130" width="60" height="45" rx="6" fill="#9ef" stroke="#cff" stroke-width="1.2" />
    <rect x="-22" y="-120" width="44" height="14" rx="2" fill="#fff" opacity="0.75" />
    """.strip()
            )
        if upgrade_stage >= 2:
            parts.append(
                f"""
    <rect x="-70" y="85" width="140" height="22" rx="6" fill="#3cf"
          filter="url(#glow_{badge_id})" opacity="0.65" />
    <rect x="-50" y="60" width="100" height="10" rx="5" fill="#7ff" opacity="0.5" />
    """.strip()
            )
        if upgrade_stage >= 3:
            parts.append(
                f'<path d="M-20 95 L0 150 L20 95 Z" fill="#ffd54f" opacity="0.8" '
                f'filter="url(#glow_{badge_id})" />'
            )
            parts.append(
                '<circle cx="0" cy="-20" r="22" fill="#ffe082" opacity="0.4" />'
            )
        return parts

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        upgrade_parts = self._upgrade_parts(badge_id, upgrade_stage)
        return f"""
<g transform="translate(0, -10)">
    <rect x="-30" y="-80" width="60" height="180" rx="10" fill="#e76" />
    <rect x="-70" y="-20" width="30" height="140" rx="5" fill="#fff" />
    <path d="M-70 -20 L-55 -50 L-40 -20 Z" fill="#fff" />
    <rect x="40" y="-20" width="30" height="140" rx="5" fill="#fff" />
    <path d="M40 -20 L55 -50 L70 -20 Z" fill="#fff" />
    <path d="M0 -40 L20 20 L20 80 L0 90 L-20 80 L-20 20 Z" fill="{hull_fill}" stroke="#333" />
    <path d="M0 -40 L15 10 L0 0 L-15 10 Z" fill="#222" />
    {''.join(upgrade_parts)}
</g>
""".strip()
