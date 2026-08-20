from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order
from ..schemas import OrderResponse

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/{order_number}", response_model=OrderResponse)
def get_order(order_number: str, db: Session = Depends(get_db)):
    order = db.scalar(select(Order).where(func.upper(Order.order_number) == order_number.upper()))
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    return order
