from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, models_ml, products, scenarios
from app.config import settings
from app.db.session import Base, engine
