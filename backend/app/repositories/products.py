from sqlalchemy.orm import Session

from app.db.models import ProductORM
from app.schemas.product import ProductCreate, ProductUpdate


def list_products(db: Session) -> list[ProductORM]:
    return db.query(ProductORM).order_by(ProductORM.created_at.desc()).all()


def get_product(db: Session, product_id: str) -> ProductORM | None:
    return db.query(ProductORM).filter(ProductORM.product_id == product_id).first()


def create_product(db: Session, payload: ProductCreate) -> ProductORM:
    row = ProductORM(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_product(db: Session, product_id: str, payload: ProductUpdate) -> ProductORM | None:
    row = get_product(db, product_id)
    if not row:
        return None
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def delete_product(db: Session, product_id: str) -> bool:
    row = get_product(db, product_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
