from typing import Any, Literal

from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    name: str
    horizon_weeks: int = Field(default=12, ge=1, le=104)
    market_config: dict[str, Any] = Field(default_factory=dict)
    product_ids: list[str] = Field(default_factory=list)


class ScenarioRead(BaseModel):
    scenario_id: str
    name: str
    horizon_weeks: int
    market_config: dict[str, Any]
    product_ids: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SimulateRequest(BaseModel):
    mode: Literal["deterministic", "monte_carlo"] = "deterministic"
    seed: int | None = 42
    n_draws: int = Field(default=200, ge=10, le=5000)


class WeeklyPointRead(BaseModel):
    week_index: int
    price: float
    quantity: float
    revenue: float
    gross_profit: float
    margin_ratio: float


class SimulationRunRead(BaseModel):
    run_id: str
    scenario_id: str
    mode: str
    seed: int | None
    total_profit: float
    series: dict[str, list[WeeklyPointRead]]


class OptimizeRequest(BaseModel):
    product_id: str
    week_index: int = 0
    p_min: float = Field(gt=0)
    p_max: float = Field(gt=0)
    min_margin_ratio: float = Field(default=0.0, ge=0, lt=1)


class OptimizeResponse(BaseModel):
    recommended_price: float
    expected_quantity: float
    expected_profit: float
    binding_constraints: list[str]
