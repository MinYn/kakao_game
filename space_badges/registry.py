from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ShipShape(str, Enum):
    SHUTTLE = "shuttle"
    ROCKET = "rocket"
    LIFTER = "lifter"
    INTERCEPTOR = "interceptor"


@dataclass(frozen=True)
class BadgeVariant:
    name: str
    sub: str
    shape: ShipShape
    color: str


VARIANTS: list[BadgeVariant] = [
    BadgeVariant(name="ORION-X", sub="FLT-101", shape=ShipShape.SHUTTLE, color="white"),
    BadgeVariant(name="TITAN-V", sub="HEAVY", shape=ShipShape.ROCKET, color="silver"),
    BadgeVariant(name="AETHER", sub="MK-IV", shape=ShipShape.INTERCEPTOR, color="dark"),
    BadgeVariant(name="VOYAGER", sub="DEEP", shape=ShipShape.SHUTTLE, color="gold"),
    BadgeVariant(name="ZENITH", sub="APOLLO", shape=ShipShape.ROCKET, color="white"),
    BadgeVariant(name="ECLIPSE", sub="STEALTH", shape=ShipShape.INTERCEPTOR, color="black"),
    BadgeVariant(name="ATLAS", sub="CARGO", shape=ShipShape.LIFTER, color="orange"),
    BadgeVariant(name="NOVA", sub="PRIME", shape=ShipShape.SHUTTLE, color="blue"),
    BadgeVariant(name="HELIOS", sub="SOLAR", shape=ShipShape.ROCKET, color="gold"),
    BadgeVariant(name="VANGUARD", sub="SSTO", shape=ShipShape.LIFTER, color="silver"),
]
