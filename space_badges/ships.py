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


class PixelShipMixin:
    """Shared SVG helpers for cute side-view pixel-art ship renderers."""

    @staticmethod
    def _rect(x: int, y: int, width: int, height: int, fill: str, **attrs: str) -> str:
        attr_text = " ".join(f'{key.replace("_", "-")}="{value}"' for key, value in attrs.items())
        if attr_text:
            attr_text = f" {attr_text}"
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}"{attr_text}/>'

    @staticmethod
    def _parts(parts: list[str]) -> str:
        return "\n    ".join(parts)

    def _cute_ship_parts(
        self,
        *,
        hull_fill: str,
        badge_id: str,
        accent_fill: str,
        window_fill: str,
        frame_index: int,
        upgrade_stage: int,
        cargo: bool = False,
    ) -> list[str]:
        flame_width = 28 if frame_index % 2 == 0 else 40
        parts = [
            # chunky black pixel outline, side-view silhouette
            self._rect(-124, -56, 132, 16, "#050505"),
            self._rect(-148, -40, 204, 16, "#050505"),
            self._rect(-164, -24, 244, 48, "#050505"),
            self._rect(-148, 24, 204, 16, "#050505"),
            self._rect(-116, 40, 132, 16, "#050505"),
            self._rect(80, -8, 24, 16, "#050505"),
            self._rect(-188, -8, 24, 16, "#050505"),
            # soft, toy-like white body
            self._rect(-116, -40, 120, 16, hull_fill),
            self._rect(-140, -24, 188, 48, hull_fill),
            self._rect(-116, 24, 120, 16, hull_fill),
            self._rect(48, -8, 32, 16, hull_fill),
            # red/candy accent fins and nose, inspired by the reference image
            self._rect(-164, -56, 56, 32, accent_fill),
            self._rect(-172, -48, 16, 16, "#050505"),
            self._rect(-164, 24, 56, 32, accent_fill),
            self._rect(-172, 40, 16, 16, "#050505"),
            self._rect(-188, -8, 52, 24, accent_fill),
            self._rect(80, -16, 32, 32, accent_fill),
            self._rect(112, -8, 16, 16, "#050505"),
            # cute oversized cockpit and two portholes
            self._rect(-36, -56, 76, 16, "#050505"),
            self._rect(-52, -40, 108, 16, "#050505"),
            self._rect(-52, -24, 124, 32, "#050505"),
            self._rect(-36, 8, 92, 16, "#050505"),
            self._rect(-28, -40, 60, 16, window_fill),
            self._rect(-44, -24, 100, 32, window_fill),
            self._rect(-28, 8, 68, 8, window_fill),
            self._rect(16, -32, 16, 16, "#b8d8ff", opacity="0.9"),
            self._rect(32, -16, 16, 16, "#b8d8ff", opacity="0.75"),
            self._rect(-72, 8, 24, 24, "#2f7fd8"),
            self._rect(-64, 0, 24, 24, "#050505"),
            self._rect(-60, 4, 16, 16, "#2f7fd8"),
            self._rect(-28, 8, 24, 24, "#2f7fd8"),
            self._rect(-20, 0, 24, 24, "#050505"),
            self._rect(-16, 4, 16, 16, "#2f7fd8"),
            # small smiling highlight / shine pixels
            self._rect(-148, -36, 20, 8, "#ff8080", opacity="0.8"),
            self._rect(-132, 32, 20, 8, "#ff8080", opacity="0.7"),
            self._rect(58, -4, 12, 8, "#ffd6d6", opacity="0.75"),
            self._rect(-216, -4, flame_width, 8, "#ff6d00", opacity="0.9"),
            self._rect(-216, 8, max(16, flame_width - 12), 8, "#ffd54f", opacity="0.95"),
        ]
        if cargo:
            parts.extend([
                self._rect(-96, 32, 56, 16, "#b0bec5"),
                self._rect(-96, 48, 40, 8, "#eceff1"),
            ])
        if upgrade_stage >= 1:
            parts.extend([
                self._rect(-92, -64, 16, 24, "#40e0d0", filter=f"url(#glow_{badge_id})"),
                self._rect(-100, -72, 32, 8, "#050505"),
            ])
        if upgrade_stage >= 2:
            parts.extend([
                self._rect(-88, 40, 24, 32, "#40e0d0", opacity="0.8"),
                self._rect(-32, 40, 24, 32, "#40e0d0", opacity="0.8"),
            ])
        if upgrade_stage >= 3:
            parts.extend([
                self._rect(0, -76, 32, 16, "#ffd54f", filter=f"url(#glow_{badge_id})"),
                self._rect(8, -84, 16, 8, "#fff59d"),
            ])
        return parts


class ShuttleShip(PixelShipMixin, ShipRenderer):
    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        parts = self._cute_ship_parts(
            hull_fill="#fff7ef" if color != "black" else "#303038",
            badge_id=badge_id,
            accent_fill="#d62839",
            window_fill="#8fb7ff",
            frame_index=frame_index,
            upgrade_stage=upgrade_stage,
        )
        return f'<g transform="translate(26, -4)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'


class RocketShip(PixelShipMixin, ShipRenderer):
    def render(self, hull_fill: str, badge_id: str, color: str, frame_index: int = 0, upgrade_stage: int = 0) -> str:
        parts = self._cute_ship_parts(
            hull_fill="#fffaf2" if color != "black" else "#303038",
            badge_id=badge_id,
            accent_fill="#ff7043",
            window_fill="#93c5fd",
            frame_index=frame_index,
            upgrade_stage=upgrade_stage,
        )
        parts.extend([self._rect(-168, -72, 40, 16, "#ff7043"), self._rect(-168, 56, 40, 16, "#ff7043")])
        return f'<g transform="translate(34, -2)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'


class InterceptorShip(PixelShipMixin, ShipRenderer):
    def render(self, hull_fill: str, badge_id: str, color: str, frame_index: int = 0, upgrade_stage: int = 0) -> str:
        parts = self._cute_ship_parts(
            hull_fill="#f5f3ff" if color != "black" else "#27272a",
            badge_id=badge_id,
            accent_fill="#7c3aed",
            window_fill="#a5b4fc",
            frame_index=frame_index,
            upgrade_stage=upgrade_stage,
        )
        parts.extend([self._rect(-132, -72, 88, 16, "#7c3aed"), self._rect(-132, 56, 88, 16, "#7c3aed")])
        return f'<g transform="translate(34, -2)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'


class LifterShip(PixelShipMixin, ShipRenderer):
    def render(self, hull_fill: str, badge_id: str, color: str, frame_index: int = 0, upgrade_stage: int = 0) -> str:
        parts = self._cute_ship_parts(
            hull_fill="#fff7ed",
            badge_id=badge_id,
            accent_fill="#f97316",
            window_fill="#7dd3fc",
            frame_index=frame_index,
            upgrade_stage=upgrade_stage,
            cargo=True,
        )
        parts.extend([self._rect(-172, -72, 32, 16, "#f97316"), self._rect(-172, 56, 32, 16, "#f97316")])
        return f'<g transform="translate(34, -2)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'
