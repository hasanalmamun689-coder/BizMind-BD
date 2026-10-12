from decimal import Decimal
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.schemas.sale import SaleCreate, SaleOut, SalesSummaryOut

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("", response_model=list[SaleOut])
def list_sales(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Sale).filter(Sale.business_id == current_user.business_id).order_by(Sale.sold_at.desc()).all()


@router.post("", response_model=SaleOut)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Sale must include at least one item")

    sale = Sale(business_id=current_user.business_id, customer_id=payload.customer_id, created_by_id=current_user.id, total_amount=Decimal("0"))
    db.add(sale)
    db.flush()

    total = Decimal("0")
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.business_id == current_user.business_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.current_stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

        line_total = item.unit_price * item.quantity
        total += line_total
        product.current_stock -= item.quantity

        db.add(SaleItem(sale_id=sale.id, product_id=item.product_id, quantity=item.quantity, unit_price=item.unit_price, line_total=line_total))

    sale.total_amount = total
    db.commit()
    db.refresh(sale)
    return sale


@router.get("/summary", response_model=SalesSummaryOut)
def sales_summary(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    sales = (
        db.query(Sale)
        .filter(Sale.business_id == current_user.business_id, Sale.sold_at >= cutoff, Sale.status == "completed")
        .all()
    )
    total_revenue = sum((s.total_amount for s in sales), Decimal("0"))
    total_orders = len(sales)
    units_sold = sum(item.quantity for s in sales for item in s.items)
    avg_order_value = (total_revenue / total_orders) if total_orders else Decimal("0")

    return SalesSummaryOut(
        total_revenue=total_revenue,
        total_orders=total_orders,
        average_order_value=avg_order_value,
        units_sold=units_sold,
    )
