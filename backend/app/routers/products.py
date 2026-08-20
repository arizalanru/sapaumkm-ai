from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas import ProductResponse

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return db.scalars(select(Product).order_by(Product.id)).all()
