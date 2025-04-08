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
