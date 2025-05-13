"""Constant-elasticity demand with seasonality and promo multipliers."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DemandParams:
    q0: float
    p0: float
    elasticity: float
    unit_cost: float

    def __post_init__(self) -> None:
        if self.q0 <= 0:
            raise ValueError("q0 must be positive")
        if self.p0 <= 0:
            raise ValueError("p0 must be positive")
        if self.elasticity <= 0:
            raise ValueError("elasticity must be positive")
        if self.unit_cost < 0:
            raise ValueError("unit_cost must be non-negative")


def seasonality_multiplier(week_index: int, amplitude: float = 0.15) -> float:
    """Simple annual seasonality using week-of-year sine wave."""
    angle = 2.0 * math.pi * (week_index % 52) / 52.0
    return 1.0 + amplitude * math.sin(angle)


def promo_multiplier(active: bool, lift: float = 1.25) -> float:
    return lift if active else 1.0


