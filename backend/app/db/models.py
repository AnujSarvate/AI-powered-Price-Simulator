"""ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ProductORM(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    unit_cost: Mapped[float] = mapped_column(Float)
    list_price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(64), default="general")
    elasticity: Mapped[float] = mapped_column(Float)
    q0: Mapped[float] = mapped_column(Float, default=100.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScenarioORM(Base):
    __tablename__ = "scenarios"

    scenario_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    horizon_weeks: Mapped[int] = mapped_column(Integer, default=12)
    market_config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SimulationRunORM(Base):
    __tablename__ = "simulation_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scenario_id: Mapped[str] = mapped_column(String(36), index=True)
    mode: Mapped[str] = mapped_column(String(32))
