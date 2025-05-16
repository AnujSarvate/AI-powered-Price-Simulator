"""Weekly pricing simulation engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

from app.core.demand import DemandParams, demand_qty


@dataclass
class PromoWindow:
    start_week: int
    end_week: int
    active: bool = True


@dataclass
class ProductScenario:
    product_id: str
    name: str
    params: DemandParams
    price_path: list[float] | None = None
    promos: list[PromoWindow] = field(default_factory=list)


@dataclass
class WeeklyPoint:
    week_index: int
    price: float
    quantity: float
    revenue: float
    gross_profit: float
    margin_ratio: float


@dataclass
class SimulationResult:
    mode: Literal["deterministic", "monte_carlo"]
    seed: int | None
    series: dict[str, list[WeeklyPoint]]
    total_profit: float


def _promo_active(promos: list[PromoWindow], week: int) -> bool:
    return any(p.active and p.start_week <= week <= p.end_week for p in promos)


def simulate_deterministic(
    products: list[ProductScenario],
    horizon_weeks: int,
    *,
    seed: int | None = None,
) -> SimulationResult:
    if horizon_weeks < 1:
        raise ValueError("horizon_weeks must be >= 1")

    series: dict[str, list[WeeklyPoint]] = {}
    total_profit = 0.0
