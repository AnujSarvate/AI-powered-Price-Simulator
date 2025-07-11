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
