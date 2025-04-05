from sqlalchemy.orm import Session

from app.db.models import ScenarioORM, SimulationRunORM
from app.schemas.scenario import ScenarioCreate


def list_scenarios(db: Session) -> list[ScenarioORM]:
    return db.query(ScenarioORM).order_by(ScenarioORM.created_at.desc()).all()


def get_scenario(db: Session, scenario_id: str) -> ScenarioORM | None:
    return db.query(ScenarioORM).filter(ScenarioORM.scenario_id == scenario_id).first()


def create_scenario(db: Session, payload: ScenarioCreate) -> ScenarioORM:
    data = payload.model_dump()
    product_ids = data.pop("product_ids", [])
    market = data.get("market_config") or {}
