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
    """Shared SVG helpers for blocky pixel-art ship renderers."""

    @staticmethod
    def _rect(x: int, y: int, width: int, height: int, fill: str, **attrs: str) -> str:
        attr_text = " ".join(f'{key.replace("_", "-")}="{value}"' for key, value in attrs.items())
        if attr_text:
            attr_text = f" {attr_text}"
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}"{attr_text}/>'

    @staticmethod
    def _parts(parts: list[str]) -> str:
        return "\n    ".join(parts)


class ShuttleShip(PixelShipMixin, ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.extend([
                self._rect(-8, -56, 16, 48, "#455", opacity="0.75"),
                self._rect(-4, -180, 8, 28, "#777"),
                self._rect(-8, -188, 16, 8, "#0ff", filter=f"url(#glow_{badge_id})"),
            ])
        if upgrade_stage >= 2:
            parts.extend([
                self._rect(-100, 56, 32, 24, "#445"),
                self._rect(68, 56, 32, 24, "#445"),
            ])
        if upgrade_stage >= 3:
            parts.extend([
                self._rect(-60, 60, 20, 52, "#2dd", opacity="0.65"),
                self._rect(40, 60, 20, 52, "#2dd", opacity="0.65"),
            ])
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
        flame_height = 40 if frame_index % 2 == 0 else 56
        parts = [
            self._rect(-12, -156, 24, 16, tile_fill),
            self._rect(-24, -140, 48, 36, hull_fill),
            self._rect(-36, -104, 72, 52, hull_fill),
            self._rect(-44, -52, 88, 132, hull_fill),
            self._rect(-32, 80, 64, 36, hull_fill),
            self._rect(-132, 48, 40, 52, hull_fill),
            self._rect(-92, 24, 48, 64, hull_fill),
            self._rect(92, 48, 40, 52, hull_fill),
            self._rect(44, 24, 48, 64, hull_fill),
            self._rect(-20, -24, 40, 20, "#112244", stroke="#5af", stroke_width="2"),
            self._rect(-4, 28, 8, 76, "#dfe7ff", opacity="0.75"),
            *self._upgrade_parts(badge_id, upgrade_stage),
            self._rect(-24, 116, 16, flame_height, "#22aaff", opacity="0.75"),
            self._rect(8, 116, 16, flame_height, "#22aaff", opacity="0.75"),
        ]
        return f'<g transform="translate(0, -20)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'


class RocketShip(PixelShipMixin, ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.extend([self._rect(-48, 24, 12, 84, "#666"), self._rect(36, 24, 12, 84, "#666")])
        if upgrade_stage >= 2:
            parts.extend([self._rect(-68, 88, 32, 40, "#444"), self._rect(36, 88, 32, 40, "#444")])
        if upgrade_stage >= 3:
            parts.append(self._rect(-20, 28, 40, 32, "#ffd54f", opacity="0.55", filter=f"url(#glow_{badge_id})"))
        return parts

    def render(self, hull_fill: str, badge_id: str, color: str, frame_index: int = 0, upgrade_stage: int = 0) -> str:
        flame_height = 52 if frame_index % 2 == 0 else 72
        parts = [
            self._rect(-8, -148, 16, 32, "#cfd8dc"),
            self._rect(-16, -116, 32, 36, hull_fill),
            self._rect(-28, -80, 56, 188, hull_fill),
            self._rect(-28, 8, 56, 8, "#222"),
            self._rect(-28, 80, 56, 8, "#222"),
            self._rect(-60, 96, 32, 56, hull_fill),
            self._rect(28, 96, 32, 56, hull_fill),
            *self._upgrade_parts(badge_id, upgrade_stage),
            self._rect(-16, 108, 32, 40, "#222"),
            self._rect(-12, 148, 24, flame_height, "#ff6d00", opacity="0.85"),
            self._rect(-6, 148, 12, max(24, flame_height - 16), "#ffd54f", opacity="0.9"),
        ]
        return f'<g transform="translate(0, -30)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'


class InterceptorShip(PixelShipMixin, ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.extend([self._rect(-132, 36, 48, 36, "#445"), self._rect(84, 36, 48, 36, "#445")])
        if upgrade_stage >= 2:
            parts.append(self._rect(-8, -148, 16, 32, "#ccd"))
        if upgrade_stage >= 3:
            parts.append(self._rect(-16, -28, 32, 24, "#55f", opacity="0.55", filter=f"url(#glow_{badge_id})"))
        return parts

    def render(self, hull_fill: str, badge_id: str, color: str, frame_index: int = 0, upgrade_stage: int = 0) -> str:
        parts = [
            self._rect(-12, -124, 24, 48, hull_fill),
            self._rect(-24, -76, 48, 64, hull_fill),
            self._rect(-32, -12, 64, 112, hull_fill),
            self._rect(-104, 28, 72, 40, hull_fill),
            self._rect(-88, 68, 56, 32, hull_fill),
            self._rect(32, 28, 72, 40, hull_fill),
            self._rect(32, 68, 56, 32, hull_fill),
            *self._upgrade_parts(badge_id, upgrade_stage),
            self._rect(-12, -56, 24, 48, "#112244", stroke="#5af", stroke_width="2"),
            self._rect(-36, 100, 12, 16, "#0ff", filter=f"url(#glow_{badge_id})"),
            self._rect(24, 100, 12, 16, "#0ff", filter=f"url(#glow_{badge_id})"),
        ]
        return f'<g transform="translate(0, 0)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'


class LifterShip(PixelShipMixin, ShipRenderer):
    def _upgrade_parts(self, badge_id: str, upgrade_stage: int) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.extend([self._rect(-88, -8, 24, 88, "#99f"), self._rect(64, -8, 24, 88, "#99f")])
        if upgrade_stage >= 2:
            parts.append(self._rect(-12, -116, 24, 36, "#ddf"))
        if upgrade_stage >= 3:
            parts.append(self._rect(-10, 100, 20, 44, "#0ff", opacity="0.55", filter=f"url(#glow_{badge_id})"))
        return parts

    def render(self, hull_fill: str, badge_id: str, color: str, frame_index: int = 0, upgrade_stage: int = 0) -> str:
        parts = [
            self._rect(-32, -84, 64, 184, "#e76"),
            self._rect(-72, -20, 32, 140, "#fff"),
            self._rect(-64, -52, 16, 32, "#fff"),
            self._rect(40, -20, 32, 140, "#fff"),
            self._rect(48, -52, 16, 32, "#fff"),
            *self._upgrade_parts(badge_id, upgrade_stage),
            self._rect(-20, -44, 40, 24, "#222"),
            self._rect(-24, -20, 48, 100, hull_fill, stroke="#333", stroke_width="2"),
            self._rect(-12, 80, 24, 20, hull_fill),
        ]
        return f'<g transform="translate(0, -10)" shape-rendering="crispEdges">\n    {self._parts(parts)}\n</g>'
