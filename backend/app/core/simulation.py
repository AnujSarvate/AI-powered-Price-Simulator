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

    for prod in products:
        points: list[WeeklyPoint] = []
        for t in range(horizon_weeks):
            if prod.price_path and t < len(prod.price_path):
                price = prod.price_path[t]
            else:
                price = prod.params.p0
            promo = _promo_active(prod.promos, t)
            qty = demand_qty(price, t, prod.params, promo_active=promo)
            revenue = price * qty
            profit = (price - prod.params.unit_cost) * qty
            margin = (price - prod.params.unit_cost) / price if price else 0.0
            points.append(
                WeeklyPoint(
                    week_index=t,
                    price=price,
                    quantity=qty,
                    revenue=revenue,
                    gross_profit=profit,
                    margin_ratio=margin,
                )
            )
            total_profit += profit
        series[prod.product_id] = points

    return SimulationResult(
        mode="deterministic",
        seed=seed,
        series=series,
        total_profit=total_profit,
    )


def simulate_monte_carlo(
    products: list[ProductScenario],
    horizon_weeks: int,
    *,
    n_draws: int = 200,
    seed: int = 42,
    elasticity_sigma: float = 0.05,
    q0_sigma: float = 0.08,
) -> SimulationResult:
    rng = random.Random(seed)
    profits: list[float] = []

    for _ in range(n_draws):
        drawn: list[ProductScenario] = []
        for p in products:
            eps = max(0.05, rng.gauss(p.params.elasticity, elasticity_sigma))
            q0 = max(0.01, rng.gauss(p.params.q0, q0_sigma * p.params.q0))
            drawn.append(
                ProductScenario(
                    product_id=p.product_id,
                    name=p.name,
                    params=DemandParams(
                        q0=q0,
                        p0=p.params.p0,
                        elasticity=eps,
                        unit_cost=p.params.unit_cost,
                    ),
                    price_path=p.price_path,
                    promos=p.promos,
                )
            )
        res = simulate_deterministic(drawn, horizon_weeks)
