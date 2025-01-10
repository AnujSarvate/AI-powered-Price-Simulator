from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import products as repo
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[ProductRead]:
    return repo.list_products(db)


@router.post("", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    return repo.create_product(db, payload)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: str, db: Session = Depends(get_db)) -> ProductRead:
    row = repo.get_product(db, product_id)
    if not row:
        raise HTTPException(status_code=404, detail="product not found")
    return row


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: str, payload: ProductUpdate, db: Session = Depends(get_db)
) -> ProductRead:
    row = repo.update_product(db, product_id, payload)
    if not row:
        raise HTTPException(status_code=404, detail="product not found")
    return row


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: str, db: Session = Depends(get_db)) -> None:
    if not repo.delete_product(db, product_id):
        raise HTTPException(status_code=404, detail="product not found")
