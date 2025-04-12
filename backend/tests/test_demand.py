import pytest

from app.core.demand import DemandParams, demand_qty


def test_demand_decreases_when_price_increases():
    params = DemandParams(q0=100, p0=10, elasticity=1.5, unit_cost=4)
    low = demand_qty(10, 0, params)
    high = demand_qty(15, 0, params)
    assert high < low


def test_invalid_elasticity():
    with pytest.raises(ValueError):
        DemandParams(q0=100, p0=10, elasticity=0, unit_cost=4)
