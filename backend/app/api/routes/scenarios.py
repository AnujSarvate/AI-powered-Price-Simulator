from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import scenarios as repo
from app.schemas.scenario import (
    OptimizeRequest,
    OptimizeResponse,
    ScenarioCreate,
    ScenarioRead,
    SimulateRequest,
    SimulationRunRead,
    WeeklyPointRead,
)
from app.services import scenario_service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _scenario_read(row) -> ScenarioRead:
    cfg = row.market_config or {}
    return ScenarioRead(
        scenario_id=row.scenario_id,
        name=row.name,
        horizon_weeks=row.horizon_weeks,
        market_config=cfg,
        product_ids=cfg.get("product_ids") or [],
    )


@router.get("", response_model=list[ScenarioRead])
def list_scenarios(db: Session = Depends(get_db)) -> list[ScenarioRead]:
    return [_scenario_read(s) for s in repo.list_scenarios(db)]


@router.post("", response_model=ScenarioRead, status_code=201)
def create_scenario(payload: ScenarioCreate, db: Session = Depends(get_db)) -> ScenarioRead:
    row = scenario_service.create_scenario(db, payload)
    return _scenario_read(row)


@router.post("/{scenario_id}/simulate", response_model=SimulationRunRead)
