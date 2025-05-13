"""Constant-elasticity demand with seasonality and promo multipliers."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DemandParams:
    q0: float
    p0: float
