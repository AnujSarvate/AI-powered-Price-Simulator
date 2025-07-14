from sqlalchemy.orm import Session

from app.core.demand import DemandParams
from app.core.optimizer import PriceConstraints, optimize_price
from app.core.simulation import ProductScenario, PromoWindow, simulate_deterministic, simulate_monte_carlo
from app.repositories import products as product_repo
