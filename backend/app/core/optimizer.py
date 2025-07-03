"""Price optimization under box constraints."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.demand import DemandParams, demand_qty


@dataclass(frozen=True)
class PriceConstraints:
    p_min: float
