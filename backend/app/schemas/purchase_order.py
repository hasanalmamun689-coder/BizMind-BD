from decimal import Decimal
from pydantic import BaseModel

from app.models.enums import PurchaseOrderStatus


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_cost: Decimal


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    reason: str | None = None
    items: list[PurchaseOrderItemCreate]


class PurchaseOrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_cost: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class PurchaseOrderOut(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    status: PurchaseOrderStatus
    total_cost: Decimal
    reason: str | None
    items: list[PurchaseOrderItemOut] = []

    class Config:
        from_attributes = True
