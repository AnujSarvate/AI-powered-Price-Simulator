from sqlalchemy.orm import Session

from app.core.demand import DemandParams
from app.core.optimizer import PriceConstraints, optimize_price
from app.core.simulation import ProductScenario, PromoWindow, simulate_deterministic, simulate_monte_carlo
from app.repositories import products as product_repo
from app.repositories import scenarios as scenario_repo
from app.schemas.scenario import OptimizeRequest, ScenarioCreate, SimulateRequest


def _products_for_scenario(db: Session, scenario) -> list[ProductScenario]:
    cfg = scenario.market_config or {}
