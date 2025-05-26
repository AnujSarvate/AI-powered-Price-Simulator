from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import products as repo
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
