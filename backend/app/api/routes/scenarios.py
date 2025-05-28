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
def simulate_scenario(
    scenario_id: str, payload: SimulateRequest, db: Session = Depends(get_db)
) -> SimulationRunRead:
    try:
        out = scenario_service.run_simulation(db, scenario_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not out:
        raise HTTPException(status_code=404, detail="scenario not found")
    run, result = out
    series = {
        pid: [WeeklyPointRead(**pt) for pt in points]
        for pid, points in result["series"].items()
    }
    return SimulationRunRead(
        run_id=run.run_id,
        scenario_id=scenario_id,
        mode=run.mode,
        seed=run.seed,
        total_profit=result["total_profit"],
        series=series,
    )


@router.get("/runs/{run_id}", response_model=SimulationRunRead)
def get_run(run_id: str, db: Session = Depends(get_db)) -> SimulationRunRead:
    run = repo.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    result = run.result
    series = {
        pid: [WeeklyPointRead(**pt) for pt in points]
        for pid, points in result["series"].items()
    }
    return SimulationRunRead(
        run_id=run.run_id,
        scenario_id=run.scenario_id,
        mode=run.mode,
        seed=run.seed,
        total_profit=result["total_profit"],
        series=series,
    )


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(payload: OptimizeRequest, db: Session = Depends(get_db)) -> OptimizeResponse:
    try:
        res = scenario_service.run_optimize(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not res:
        raise HTTPException(status_code=404, detail="product not found")
    return OptimizeResponse(
        recommended_price=res.recommended_price,
        expected_quantity=res.expected_quantity,
        expected_profit=res.expected_profit,
        binding_constraints=res.binding_constraints,
    )
