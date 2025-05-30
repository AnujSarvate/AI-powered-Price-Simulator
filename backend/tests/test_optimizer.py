from app.core.demand import DemandParams
from app.core.optimizer import PriceConstraints, closed_form_optimum, optimize_price


def test_closed_form_matches_grid():
    params = DemandParams(q0=100, p0=20, elasticity=2.0, unit_cost=5)
    analytic = closed_form_optimum(params)
    assert analytic is not None
    res = optimize_price(
        0,
        params,
        PriceConstraints(p_min=1, p_max=100, min_margin_ratio=0),
    )
    assert abs(res.recommended_price - analytic) < 0.5
