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
    BadgeVariant(name="MOMO-1", sub="BEEP", shape=ShipShape.SHUTTLE, color="white"),
    BadgeVariant(name="BERRY", sub="POP", shape=ShipShape.ROCKET, color="silver"),
    BadgeVariant(name="BUBBLE", sub="BOO", shape=ShipShape.INTERCEPTOR, color="dark"),
    BadgeVariant(name="COOKIE", sub="YUM", shape=ShipShape.SHUTTLE, color="gold"),
    BadgeVariant(name="PUDDING", sub="PON", shape=ShipShape.ROCKET, color="white"),
    BadgeVariant(name="CANDY", sub="NOM", shape=ShipShape.INTERCEPTOR, color="black"),
    BadgeVariant(name="PEACHY", sub="CARGO", shape=ShipShape.LIFTER, color="orange"),
    BadgeVariant(name="NOVA-BUN", sub="HOP", shape=ShipShape.SHUTTLE, color="blue"),
    BadgeVariant(name="SUNNY", sub="SOL", shape=ShipShape.ROCKET, color="gold"),
    BadgeVariant(name="JELLY", sub="SSTO", shape=ShipShape.LIFTER, color="silver"),
]
