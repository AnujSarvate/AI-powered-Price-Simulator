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
    recommended_price: float
    expected_quantity: float
    expected_profit: float
    binding_constraints: list[str]


def closed_form_optimum(params: DemandParams) -> float | None:
    eps = params.elasticity
    if eps <= 1.0:
        return None
    return params.unit_cost * eps / (eps - 1.0)


def profit_at_price(price: float, week_index: int, params: DemandParams) -> tuple[float, float]:
    qty = demand_qty(price, week_index, params)
    profit = (price - params.unit_cost) * qty
    return qty, profit


def optimize_price(
    week_index: int,
    params: DemandParams,
    constraints: PriceConstraints,
    *,
    grid_steps: int = 200,
) -> OptimizeResult:
    binding: list[str] = []

    analytic = closed_form_optimum(params)
    candidates: list[float] = []
    if analytic is not None:
        candidates.append(analytic)

    lo, hi = constraints.p_min, constraints.p_max
    if lo >= hi:
        raise ValueError("p_min must be less than p_max")

    step = (hi - lo) / max(grid_steps - 1, 1)
    for i in range(grid_steps):
        candidates.append(lo + i * step)

    best_p = lo
    best_q = 0.0
    best_profit = float("-inf")

    for p in candidates:
        if p < constraints.p_min or p > constraints.p_max:
            continue
        from app.core.demand import margin_ratio

        if margin_ratio(p, params.unit_cost) < constraints.min_margin_ratio:
            continue
        q, prof = profit_at_price(p, week_index, params)
        if prof > best_profit:
            best_profit = prof
            best_p = p
            best_q = q

    if best_profit == float("-inf"):
        raise ValueError("no feasible price under constraints")

    if abs(best_p - constraints.p_min) < 1e-9:
        binding.append("p_min")
    if abs(best_p - constraints.p_max) < 1e-9:
        binding.append("p_max")

    return OptimizeResult(
        recommended_price=best_p,
        expected_quantity=best_q,
        expected_profit=best_profit,
        binding_constraints=binding,
    )
