from sqlalchemy.orm import Session

from app.core.demand import DemandParams
from app.core.optimizer import PriceConstraints, optimize_price
from app.core.simulation import ProductScenario, PromoWindow, simulate_deterministic, simulate_monte_carlo
from app.repositories import products as product_repo
from app.repositories import scenarios as scenario_repo
from app.schemas.scenario import OptimizeRequest, ScenarioCreate, SimulateRequest


def _products_for_scenario(db: Session, scenario) -> list[ProductScenario]:
    cfg = scenario.market_config or {}
    ids: list[str] = cfg.get("product_ids") or []
    promos_cfg = cfg.get("promos") or []

    out: list[ProductScenario] = []
    for pid in ids:
        row = product_repo.get_product(db, pid)
        if not row:
            continue
        promos = [
            PromoWindow(start_week=p["start_week"], end_week=p["end_week"], active=p.get("active", True))
            for p in promos_cfg
            if p.get("product_id") == pid
        ]
        out.append(
            ProductScenario(
                product_id=row.product_id,
                name=row.name,
                params=DemandParams(
                    q0=row.q0,
                    p0=row.list_price,
                    elasticity=row.elasticity,
                    unit_cost=row.unit_cost,
                ),
                promos=promos,
            )
        )
    return out


def create_scenario(db: Session, payload: ScenarioCreate):
    return scenario_repo.create_scenario(db, payload)


def run_simulation(db: Session, scenario_id: str, req: SimulateRequest):
    scenario = scenario_repo.get_scenario(db, scenario_id)
    if not scenario:
        return None
    products = _products_for_scenario(db, scenario)
    if not products:
        raise ValueError("scenario has no valid products")

    if req.mode == "monte_carlo":
        result = simulate_monte_carlo(
            products,
            scenario.horizon_weeks,
            n_draws=req.n_draws,
            seed=req.seed or 42,
        )
    else:
        result = simulate_deterministic(products, scenario.horizon_weeks, seed=req.seed)

    payload = {
        "total_profit": result.total_profit,
        "series": {
            pid: [p.__dict__ for p in points] for pid, points in result.series.items()
        },
    }
    run = scenario_repo.save_run(
        db,
        scenario_id=scenario_id,
        mode=result.mode,
        seed=result.seed,
        result=payload,
    )
    return run, payload


def run_optimize(db: Session, req: OptimizeRequest):
    row = product_repo.get_product(db, req.product_id)
    if not row:
        return None
    params = DemandParams(
        q0=row.q0,
        p0=row.list_price,
        elasticity=row.elasticity,
        unit_cost=row.unit_cost,
    )
    constraints = PriceConstraints(
        p_min=req.p_min,
        p_max=req.p_max,
        min_margin_ratio=req.min_margin_ratio,
    )
    return optimize_price(req.week_index, params, constraints)
