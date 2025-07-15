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
