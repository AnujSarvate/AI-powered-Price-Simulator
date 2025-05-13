"""Price optimization under box constraints."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.demand import DemandParams, demand_qty


@dataclass(frozen=True)
class PriceConstraints:
    p_min: float
    p_max: float
    min_margin_ratio: float = 0.0


@dataclass(frozen=True)
class OptimizeResult:
