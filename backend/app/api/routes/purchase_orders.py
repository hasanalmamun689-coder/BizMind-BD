import random
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_owner
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.enums import PurchaseOrderStatus
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderOut

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


def _generate_po_number() -> str:
    from datetime import datetime
    return f"PO-{datetime.utcnow().year}-{random.randint(10000, 99999)}"


@router.get("/purchase-orders", response_model=list[PurchaseOrderOut])
def list_purchase_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(PurchaseOrder).filter(PurchaseOrder.business_id == current_user.business_id).all()


@router.post("/purchase-orders", response_model=PurchaseOrderOut)
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Creates a purchase order in DRAFT status. Per the human-in-the-loop
    principle (blueprint section 17), it must be explicitly approved before
    it becomes an actionable order — see /approve below.
    """
    po = PurchaseOrder(
        business_id=current_user.business_id,
        supplier_id=payload.supplier_id,
        created_by_id=current_user.id,
        po_number=_generate_po_number(),
        status=PurchaseOrderStatus.DRAFT,
        reason=payload.reason,
        total_cost=Decimal("0"),
    )
    db.add(po)
    db.flush()

    total = Decimal("0")
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.business_id == current_user.business_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        line_total = item.unit_cost * item.quantity
        total += line_total
        db.add(PurchaseOrderItem(purchase_order_id=po.id, product_id=item.product_id, quantity=item.quantity, unit_cost=item.unit_cost, line_total=line_total))

    po.total_cost = total
    db.commit()
    db.refresh(po)
    return po


@router.post("/purchase-orders/{po_id}/approve", response_model=PurchaseOrderOut)
def approve_purchase_order(po_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_owner)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.business_id == current_user.business_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = PurchaseOrderStatus.APPROVED
    po.approved_by_id = current_user.id
    db.commit()
    db.refresh(po)
    return po


@router.post("/purchase-orders/{po_id}/reject", response_model=PurchaseOrderOut)
def reject_purchase_order(po_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_owner)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.business_id == current_user.business_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = PurchaseOrderStatus.REJECTED
    db.commit()
    db.refresh(po)
    return po
