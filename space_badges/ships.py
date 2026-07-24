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
    """Shared SVG helpers for side-view pixel-art ship renderers.

    Art is original rect-pixel construction (not embedded sprites).
    Silhouettes re-interpret common free pixel-spaceship tropes:
    shuttle = stubby transport, rocket = slim cone, interceptor = delta fighter,
    lifter = boxy hauler. See docs/assets/REFERENCES.md.
    """

    OUTLINE = "#050505"
    HIGHLIGHT = "#ffffff"
    SHADOW = "#1a1a22"
    FLAME_CORE = "#fff59d"
    FLAME_MID = "#ff9100"
    FLAME_OUTER = "#ff3d00"
    PORTHOLE = "#2f7fd8"
    GLASS_HI = "#e0f2fe"

    @staticmethod
    def _rect(x: int, y: int, width: int, height: int, fill: str, **attrs: str) -> str:
        attr_text = " ".join(f'{key.replace("_", "-")}="{value}"' for key, value in attrs.items())
        if attr_text:
            attr_text = f" {attr_text}"
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}"{attr_text}/>'

    @staticmethod
    def _parts(parts: list[str]) -> str:
        return "\n    ".join(parts)

    def _hull_base(self, color: str, light: str, dark: str) -> str:
        if color == "black":
            return dark
        if color == "dark":
            return "#3a3a48"
        if color == "gold":
            return "#f5e6a8"
        if color == "blue":
            return "#c8daf8"
        if color == "orange":
            return "#ffe0c2"
        if color == "silver":
            return "#d8dde6"
        return light

    def _plume(self, frame_index: int, x: int = -200, y: int = -12) -> list[str]:
        """Two-frame thruster plume (length alternates)."""
        outer_w = 36 if frame_index % 2 == 0 else 52
        mid_w = max(20, outer_w - 12)
        core_w = max(12, outer_w - 24)
        return [
            self._rect(x, y, outer_w, 8, self.FLAME_OUTER, opacity="0.85"),
            self._rect(x, y + 8, outer_w - 4, 8, self.FLAME_MID, opacity="0.95"),
            self._rect(x, y + 16, mid_w, 8, self.FLAME_MID, opacity="0.9"),
            self._rect(x + 4, y + 8, core_w, 8, self.FLAME_CORE, opacity="0.98"),
            self._rect(x + 8, y + 4, max(8, core_w - 8), 4, self.HIGHLIGHT, opacity="0.7"),
        ]

    def _upgrade_bits(self, badge_id: str, upgrade_stage: int, cx: int = 0) -> list[str]:
        parts: list[str] = []
        if upgrade_stage >= 1:
            parts.extend(
                [
                    self._rect(cx - 8, -84, 16, 20, "#40e0d0", filter=f"url(#glow_{badge_id})"),
                    self._rect(cx - 16, -92, 32, 8, self.OUTLINE),
                    self._rect(cx - 4, -100, 8, 8, "#a7f3d0"),
                ]
            )
        if upgrade_stage >= 2:
            parts.extend(
                [
                    self._rect(cx - 48, 48, 20, 28, "#40e0d0", opacity="0.85"),
                    self._rect(cx + 12, 48, 20, 28, "#40e0d0", opacity="0.85"),
                    self._rect(cx - 44, 72, 12, 8, self.OUTLINE),
                    self._rect(cx + 16, 72, 12, 8, self.OUTLINE),
                ]
            )
        if upgrade_stage >= 3:
            parts.extend(
                [
                    self._rect(cx - 8, -112, 16, 12, "#ffd54f", filter=f"url(#glow_{badge_id})"),
                    self._rect(cx - 4, -120, 8, 8, "#fff59d"),
                    self._rect(cx - 20, -108, 8, 8, "#ffd54f", opacity="0.8"),
                    self._rect(cx + 12, -108, 8, 8, "#ffd54f", opacity="0.8"),
                ]
            )
        return parts

    def _wrap(self, parts: list[str], tx: int = 0, ty: int = 0) -> str:
        return (
            f'<g transform="translate({tx}, {ty})" shape-rendering="crispEdges">\n'
            f"    {self._parts(parts)}\n</g>"
        )


class ShuttleShip(PixelShipMixin, ShipRenderer):
    """Stubby transport: rounded nose, fat midsection, bubble canopy, modest fins."""

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        o = self.OUTLINE
        hull = self._hull_base(color, "#fff7ef", "#303038")
        accent = "#d62839"
        accent_hi = "#ff6b6b"
        window = "#7eb6ff"
        parts: list[str] = []

        # --- outline (chunky silhouette) ---
        parts += [
            # body outline
            self._rect(-140, -48, 200, 16, o),
            self._rect(-156, -32, 248, 64, o),
            self._rect(-132, 32, 176, 16, o),
            # nose outline (blunt)
            self._rect(92, -24, 40, 48, o),
            self._rect(124, -8, 16, 16, o),
            # tail / nozzle outline
            self._rect(-180, -16, 28, 32, o),
            # upper fin outline
            self._rect(-96, -72, 48, 28, o),
            # lower fin outline
            self._rect(-96, 40, 48, 28, o),
            # canopy outline
            self._rect(-28, -64, 88, 20, o),
            self._rect(-40, -52, 112, 28, o),
        ]

        # --- hull fill ---
        parts += [
            self._rect(-132, -40, 184, 16, hull),
            self._rect(-148, -24, 232, 48, hull),
            self._rect(-124, 24, 160, 16, hull),
            # blunt nose
            self._rect(84, -16, 40, 32, hull),
            self._rect(116, 0, 16, 16, hull),
            # soft belly shade
            self._rect(-140, 16, 200, 8, self.SHADOW, opacity="0.18"),
            # top highlight strip
            self._rect(-120, -36, 140, 8, self.HIGHLIGHT, opacity="0.35"),
        ]

        # --- accent fins + nose tip ---
        parts += [
            self._rect(-88, -64, 32, 20, accent),
            self._rect(-80, -72, 16, 8, accent_hi),
            self._rect(-88, 44, 32, 20, accent),
            self._rect(-80, 56, 16, 8, o),
            self._rect(100, -8, 24, 16, accent),
            self._rect(116, 0, 16, 8, accent_hi),
        ]

        # --- engine block ---
        parts += [
            self._rect(-172, -8, 28, 16, accent),
            self._rect(-164, -16, 12, 32, "#8b1e2d"),
            self._rect(-176, -4, 8, 8, "#ffab91"),
        ]

        # --- bubble canopy ---
        parts += [
            self._rect(-20, -56, 72, 16, window),
            self._rect(-32, -44, 96, 20, window),
            self._rect(-12, -52, 24, 12, self.GLASS_HI, opacity="0.85"),
            self._rect(28, -40, 16, 12, self.GLASS_HI, opacity="0.55"),
        ]

        # --- twin portholes ---
        parts += [
            self._rect(-72, 0, 20, 20, o),
            self._rect(-68, 4, 12, 12, self.PORTHOLE),
            self._rect(-64, 4, 4, 4, self.GLASS_HI, opacity="0.8"),
            self._rect(-36, 0, 20, 20, o),
            self._rect(-32, 4, 12, 12, self.PORTHOLE),
            self._rect(-28, 4, 4, 4, self.GLASS_HI, opacity="0.8"),
        ]

        # --- tiny smile / cheek pixels ---
        parts += [
            self._rect(-148, -28, 16, 8, accent_hi, opacity="0.55"),
            self._rect(72, 8, 12, 8, accent_hi, opacity="0.45"),
        ]

        parts += self._plume(frame_index, x=-220, y=-12)
        parts += self._upgrade_bits(badge_id, upgrade_stage, cx=-16)
        return self._wrap(parts, tx=20, ty=-2)


class RocketShip(PixelShipMixin, ShipRenderer):
    """Slim missile profile: long body, pointed nose cone, stacked tanks, rear fins."""

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        o = self.OUTLINE
        hull = self._hull_base(color, "#fffaf2", "#303038")
        accent = "#ff7043"
        accent_hi = "#ffab91"
        band = "#ffcc80"
        window = "#93c5fd"
        parts: list[str] = []

        # --- outline: long horizontal rocket ---
        parts += [
            self._rect(-168, -32, 248, 64, o),
            self._rect(-152, -48, 184, 16, o),
            self._rect(-152, 32, 184, 16, o),
            # pointed nose steps
            self._rect(80, -24, 48, 48, o),
            self._rect(120, -16, 32, 32, o),
            self._rect(144, -8, 24, 16, o),
            # nozzle
            self._rect(-196, -16, 32, 32, o),
            # large rear fins (vertical character)
            self._rect(-140, -80, 36, 36, o),
            self._rect(-140, 44, 36, 36, o),
        ]

        # --- hull fill ---
        parts += [
            self._rect(-160, -24, 232, 48, hull),
            self._rect(-144, -40, 168, 16, hull),
            self._rect(-144, 24, 168, 16, hull),
            # nose cone
            self._rect(72, -16, 48, 32, hull),
            self._rect(112, -8, 32, 16, hull),
            self._rect(136, 0, 24, 8, accent),
            # longitudinal highlight
            self._rect(-140, -20, 180, 8, self.HIGHLIGHT, opacity="0.3"),
            self._rect(-148, 12, 200, 8, self.SHADOW, opacity="0.15"),
        ]

        # --- tank bands ---
        parts += [
            self._rect(-100, -24, 12, 48, band),
            self._rect(-40, -24, 12, 48, band),
            self._rect(20, -24, 12, 48, band),
        ]

        # --- fins ---
        parts += [
            self._rect(-132, -72, 24, 28, accent),
            self._rect(-124, -80, 12, 12, accent_hi),
            self._rect(-132, 44, 24, 28, accent),
            self._rect(-124, 64, 12, 12, o),
            # small mid strakes
            self._rect(-20, -48, 40, 8, accent),
            self._rect(-20, 40, 40, 8, accent),
        ]

        # --- engine ---
        parts += [
            self._rect(-188, -8, 28, 16, accent),
            self._rect(-180, -16, 16, 32, "#bf360c"),
            self._rect(-192, -4, 8, 8, accent_hi),
        ]

        # --- cockpit strip (side windows along body) ---
        parts += [
            self._rect(40, -16, 40, 24, o),
            self._rect(44, -12, 32, 16, window),
            self._rect(48, -12, 8, 8, self.GLASS_HI, opacity="0.75"),
            self._rect(-72, -8, 16, 16, o),
            self._rect(-68, -4, 8, 8, self.PORTHOLE),
            self._rect(-8, -8, 16, 16, o),
            self._rect(-4, -4, 8, 8, self.PORTHOLE),
        ]

        parts += self._plume(frame_index, x=-236, y=-12)
        parts += self._upgrade_bits(badge_id, upgrade_stage, cx=-40)
        return self._wrap(parts, tx=8, ty=0)


class InterceptorShip(PixelShipMixin, ShipRenderer):
    """Delta fighter: sharp nose, wide swept wings, twin thrusters, aggressive stance."""

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        o = self.OUTLINE
        hull = self._hull_base(color, "#f5f3ff", "#27272a")
        accent = "#7c3aed"
        accent_hi = "#a78bfa"
        wing = "#5b21b6"
        window = "#a5b4fc"
        parts: list[str] = []

        # --- outline: angular fighter ---
        parts += [
            # thin long fuselage
            self._rect(-120, -20, 200, 40, o),
            self._rect(-100, -32, 140, 12, o),
            self._rect(-100, 20, 140, 12, o),
            # needle nose
            self._rect(80, -12, 56, 24, o),
            self._rect(128, -4, 24, 8, o),
            # huge delta wings
            self._rect(-96, -88, 120, 60, o),
            self._rect(-96, 28, 120, 60, o),
            # twin nozzles
            self._rect(-156, -28, 40, 20, o),
            self._rect(-156, 8, 40, 20, o),
            # canopy spike
            self._rect(8, -44, 56, 28, o),
        ]

        # --- hull fill ---
        parts += [
            self._rect(-112, -12, 184, 24, hull),
            self._rect(-92, -24, 124, 12, hull),
            self._rect(-92, 12, 124, 12, hull),
            self._rect(72, -4, 56, 8, hull),
            self._rect(120, 0, 24, 4, accent_hi),
            self._rect(-100, -8, 160, 4, self.HIGHLIGHT, opacity="0.35"),
        ]

        # --- delta wings (stepped for pixel silhouette) ---
        parts += [
            # upper wing
            self._rect(-88, -80, 96, 48, accent),
            self._rect(-72, -88, 64, 12, wing),
            self._rect(0, -64, 32, 24, accent_hi),
            self._rect(-80, -72, 16, 8, o),
            # lower wing (mirror)
            self._rect(-88, 32, 96, 48, accent),
            self._rect(-72, 76, 64, 12, wing),
            self._rect(0, 40, 32, 24, accent_hi),
            self._rect(-80, 64, 16, 8, o),
            # wing root darken
            self._rect(-48, -28, 40, 8, wing, opacity="0.7"),
            self._rect(-48, 20, 40, 8, wing, opacity="0.7"),
        ]

        # --- twin engines ---
        parts += [
            self._rect(-148, -20, 32, 12, accent),
            self._rect(-148, 8, 32, 12, accent),
            self._rect(-156, -16, 12, 8, "#4c1d95"),
            self._rect(-156, 12, 12, 8, "#4c1d95"),
            self._rect(-160, -12, 8, 4, accent_hi),
            self._rect(-160, 16, 8, 4, accent_hi),
        ]

        # --- canopy ---
        parts += [
            self._rect(16, -36, 40, 20, window),
            self._rect(24, -40, 24, 8, window),
            self._rect(20, -32, 12, 8, self.GLASS_HI, opacity="0.8"),
            self._rect(40, -28, 8, 8, self.GLASS_HI, opacity="0.5"),
        ]

        # --- wing edge lights ---
        parts += [
            self._rect(-8, -84, 8, 8, "#f472b6"),
            self._rect(-8, 76, 8, 8, "#f472b6"),
            self._rect(24, -56, 8, 8, "#fbbf24"),
            self._rect(24, 48, 8, 8, "#fbbf24"),
        ]

        # dual plume (upper + lower engine)
        outer_w = 28 if frame_index % 2 == 0 else 40
        parts += [
            self._rect(-188, -20, outer_w, 8, self.FLAME_OUTER, opacity="0.85"),
            self._rect(-184, -16, max(12, outer_w - 10), 4, self.FLAME_CORE, opacity="0.95"),
            self._rect(-188, 12, outer_w, 8, self.FLAME_OUTER, opacity="0.85"),
            self._rect(-184, 16, max(12, outer_w - 10), 4, self.FLAME_CORE, opacity="0.95"),
            self._rect(-196, -4, outer_w - 4, 8, self.FLAME_MID, opacity="0.7"),
        ]

        parts += self._upgrade_bits(badge_id, upgrade_stage, cx=-24)
        return self._wrap(parts, tx=16, ty=0)


class LifterShip(PixelShipMixin, ShipRenderer):
    """Boxy cargo hauler: wide hull, underslung pods, thick thrusters, short nose."""

    def render(
        self,
        hull_fill: str,
        badge_id: str,
        color: str,
        frame_index: int = 0,
        upgrade_stage: int = 0,
    ) -> str:
        o = self.OUTLINE
        hull = self._hull_base(color, "#fff7ed", "#303038")
        accent = "#f97316"
        accent_hi = "#fdba74"
        cargo = "#b0bec5"
        cargo_hi = "#eceff1"
        window = "#7dd3fc"
        parts: list[str] = []

        # --- outline: blocky freighter ---
        parts += [
            # main box hull
            self._rect(-148, -48, 240, 96, o),
            self._rect(-132, -64, 160, 20, o),
            # short blunt nose
            self._rect(92, -24, 36, 48, o),
            # thick rear thruster bank
            self._rect(-188, -32, 44, 64, o),
            # cargo pods under belly
            self._rect(-100, 40, 72, 36, o),
            self._rect(-20, 40, 72, 36, o),
            # stubby top crane / bridge tower
            self._rect(-40, -88, 56, 28, o),
            # side stabilizer fins
            self._rect(-160, -72, 28, 28, o),
            self._rect(-160, 44, 28, 28, o),
        ]

        # --- hull fill ---
        parts += [
            self._rect(-140, -40, 224, 80, hull),
            self._rect(-124, -56, 144, 16, hull),
            self._rect(84, -16, 36, 32, hull),
            self._rect(-128, -36, 180, 8, self.HIGHLIGHT, opacity="0.28"),
            self._rect(-132, 24, 200, 12, self.SHADOW, opacity="0.2"),
            # panel lines
            self._rect(-60, -40, 8, 80, o, opacity="0.35"),
            self._rect(20, -40, 8, 80, o, opacity="0.35"),
        ]

        # --- bridge tower ---
        parts += [
            self._rect(-32, -80, 40, 20, accent),
            self._rect(-24, -88, 24, 12, accent_hi),
            self._rect(-16, -76, 16, 12, window),
            self._rect(-12, -76, 6, 6, self.GLASS_HI, opacity="0.8"),
        ]

        # --- cargo pods ---
        parts += [
            self._rect(-92, 48, 56, 24, cargo),
            self._rect(-84, 44, 40, 8, cargo_hi),
            self._rect(-76, 56, 12, 12, o, opacity="0.4"),
            self._rect(-12, 48, 56, 24, cargo),
            self._rect(-4, 44, 40, 8, cargo_hi),
            self._rect(4, 56, 12, 12, o, opacity="0.4"),
            # straps
            self._rect(-92, 48, 56, 4, accent, opacity="0.7"),
            self._rect(-12, 48, 56, 4, accent, opacity="0.7"),
        ]

        # --- thruster bank ---
        parts += [
            self._rect(-180, -24, 36, 48, accent),
            self._rect(-172, -32, 20, 64, "#c2410c"),
            self._rect(-184, -16, 12, 12, accent_hi),
            self._rect(-184, 4, 12, 12, accent_hi),
            self._rect(-184, 20, 12, 8, "#ffedd5"),
        ]

        # --- side fins ---
        parts += [
            self._rect(-152, -64, 16, 20, accent),
            self._rect(-152, 44, 16, 20, accent),
            self._rect(-160, -56, 12, 8, o),
            self._rect(-160, 52, 12, 8, o),
        ]

        # --- cabin windows row ---
        parts += [
            self._rect(40, -20, 36, 28, o),
            self._rect(44, -16, 28, 20, window),
            self._rect(48, -16, 8, 8, self.GLASS_HI, opacity="0.75"),
            self._rect(-100, -16, 16, 16, o),
            self._rect(-96, -12, 8, 8, self.PORTHOLE),
            self._rect(-68, -16, 16, 16, o),
            self._rect(-64, -12, 8, 8, self.PORTHOLE),
        ]

        # --- hazard stripe on nose ---
        parts += [
            self._rect(96, -8, 16, 16, accent),
            self._rect(100, -4, 8, 8, "#fbbf24"),
        ]

        # wide multi-nozzle plume
        outer_w = 40 if frame_index % 2 == 0 else 56
        parts += [
            self._rect(-224, -20, outer_w, 12, self.FLAME_OUTER, opacity="0.85"),
            self._rect(-224, 0, outer_w - 4, 12, self.FLAME_OUTER, opacity="0.85"),
            self._rect(-216, -12, max(16, outer_w - 16), 16, self.FLAME_MID, opacity="0.95"),
            self._rect(-208, -4, max(12, outer_w - 24), 8, self.FLAME_CORE, opacity="0.98"),
        ]

        parts += self._upgrade_bits(badge_id, upgrade_stage, cx=-8)
        return self._wrap(parts, tx=12, ty=-4)
