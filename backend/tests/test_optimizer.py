from app.core.demand import DemandParams
from app.core.optimizer import PriceConstraints, closed_form_optimum, optimize_price


def test_closed_form_matches_grid():
    params = DemandParams(q0=100, p0=20, elasticity=2.0, unit_cost=5)
