from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierOut, SupplierScoreOut

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Supplier).filter(Supplier.business_id == current_user.business_id).all()


@router.post("", response_model=SupplierOut)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    supplier = Supplier(business_id=current_user.business_id, **payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, payload: SupplierUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.business_id == current_user.business_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/compare", response_model=list[SupplierScoreOut])
def compare_suppliers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Weighted supplier score per blueprint section 11:
    price 30%, delivery reliability 25%, availability 20%, quality 15%, fulfillment 10%.
    Phase 1 implements the two fields we actually track (reliability_score, delivery_time_days)
    and documents the rest as a fixed baseline until purchase-history data exists to derive them.
    """
    suppliers = db.query(Supplier).filter(Supplier.business_id == current_user.business_id).all()
    results = []
    for s in suppliers:
        reliability = float(s.reliability_score) if s.reliability_score is not None else 70.0
        # Faster delivery -> higher price-proxy score (placeholder until real price history exists)
        delivery_component = max(0.0, 100 - (s.delivery_time_days or 5) * 5)
        score = round(reliability * 0.55 + delivery_component * 0.45, 1)
        results.append(
            SupplierScoreOut(
                supplier_id=s.id,
                supplier_name=s.name,
                score=score,
                price_component=delivery_component,
                reliability_component=reliability,
            )
        )
    return sorted(results, key=lambda r: r.score, reverse=True)
