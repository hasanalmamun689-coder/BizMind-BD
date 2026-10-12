from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.inventory import InventoryTransaction
from app.models.enums import InventoryTransactionType
from app.schemas.inventory import InventoryAdjustRequest, InventoryTransactionOut, StockAlertOut

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("", response_model=list[dict])
def current_inventory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    products = db.query(Product).filter(Product.business_id == current_user.business_id).all()
    return [
        {
            "product_id": p.id,
            "product_name": p.name,
            "current_stock": p.current_stock,
            "minimum_stock": p.minimum_stock,
            "maximum_stock": p.maximum_stock,
        }
        for p in products
    ]


@router.post("/adjust", response_model=InventoryTransactionOut)
def adjust_inventory(payload: InventoryAdjustRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.business_id == current_user.business_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.type == InventoryTransactionType.STOCK_IN:
        product.current_stock += payload.quantity
    elif payload.type == InventoryTransactionType.STOCK_OUT:
        if product.current_stock < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        product.current_stock -= payload.quantity
    else:  # ADJUSTMENT — quantity is the new absolute stock level
        product.current_stock = payload.quantity

    txn = InventoryTransaction(
        product_id=product.id,
        type=payload.type,
        quantity=payload.quantity,
        reason=payload.reason,
        created_by_id=current_user.id,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.get("/alerts", response_model=list[StockAlertOut])
def low_stock_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Simple heuristic stockout prediction based on trailing 30-day sales.
    This is intentionally simple — the ML forecasting service (Phase 2) replaces
    the average-daily-sales estimate with a proper demand model.
    """
    from app.models.sale import Sale, SaleItem
    from datetime import datetime, timedelta

    products = (
        db.query(Product)
        .filter(Product.business_id == current_user.business_id, Product.current_stock <= Product.minimum_stock)
        .all()
    )

    cutoff = datetime.utcnow() - timedelta(days=30)
    alerts = []
    for p in products:
        units_sold = (
            db.query(SaleItem)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .filter(SaleItem.product_id == p.id, Sale.sold_at >= cutoff)
            .all()
        )
        total_units = sum(item.quantity for item in units_sold)
        avg_daily = total_units / 30 if total_units else 0
        days_to_stockout = (p.current_stock / avg_daily) if avg_daily > 0 else None
        alerts.append(
            StockAlertOut(
                product_id=p.id,
                product_name=p.name,
                current_stock=p.current_stock,
                minimum_stock=p.minimum_stock,
                average_daily_sales=round(avg_daily, 2),
                predicted_days_to_stockout=round(days_to_stockout, 1) if days_to_stockout is not None else None,
            )
        )
    return alerts
