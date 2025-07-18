from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, models_ml, products, scenarios
from app.config import settings
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Powered Price Simulator", version=settings.app_version)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
