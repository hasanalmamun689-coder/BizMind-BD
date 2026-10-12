from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.expense import Expense
from app.schemas.analytics import DashboardSummaryOut, ProfitAnalyticsOut

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _business_health_score(sales_growth: float, profit_margin: float, low_stock_ratio: float) -> int:
    """A simple, documented weighted score (blueprint section 29 explicitly
    says the formula should be configurable/documented rather than presented
    as scientifically universal). Weights here are a starting baseline:
    sales performance 35%, profitability 35%, inventory efficiency 30%.
    """
    sales_component = max(0.0, min(100.0, 50 + sales_growth * 100))
    profit_component = max(0.0, min(100.0, 50 + profit_margin * 100))
    inventory_component = max(0.0, min(100.0, 100 - low_stock_ratio * 100))
    score = sales_component * 0.35 + profit_component * 0.35 + inventory_component * 0.30
    return round(score)


@router.get("/dashboard", response_model=DashboardSummaryOut)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff_30 = datetime.utcnow() - timedelta(days=30)
    cutoff_60 = datetime.utcnow() - timedelta(days=60)

    sales_30 = db.query(Sale).filter(Sale.business_id == current_user.business_id, Sale.sold_at >= cutoff_30).all()
    sales_prev_30 = (
        db.query(Sale)
        .filter(Sale.business_id == current_user.business_id, Sale.sold_at >= cutoff_60, Sale.sold_at < cutoff_30)
        .all()
    )

    total_sales = sum((s.total_amount for s in sales_30), Decimal("0"))
    prev_sales = sum((s.total_amount for s in sales_prev_30), Decimal("0"))
    sales_growth = float((total_sales - prev_sales) / prev_sales) if prev_sales else 0.0

    products = db.query(Product).filter(Product.business_id == current_user.business_id).all()
    inventory_value = sum((p.current_stock * p.purchase_price for p in products), Decimal("0"))
    low_stock_count = sum(1 for p in products if p.current_stock <= p.minimum_stock)
    low_stock_ratio = (low_stock_count / len(products)) if products else 0.0

    cost_of_goods = sum(
        (item.quantity * item.product.purchase_price for s in sales_30 for item in s.items),
        Decimal("0"),
    )
    expenses_30 = db.query(Expense).filter(Expense.business_id == current_user.business_id, Expense.incurred_on >= cutoff_30.date()).all()
    total_expenses = sum((e.amount for e in expenses_30), Decimal("0"))
    profit_estimate = total_sales - cost_of_goods - total_expenses
    profit_margin = float(profit_estimate / total_sales) if total_sales else 0.0

    health_score = _business_health_score(sales_growth, profit_margin, low_stock_ratio)

    return DashboardSummaryOut(
        total_sales=total_sales,
        total_profit_estimate=profit_estimate,
        inventory_value=inventory_value,
        low_stock_count=low_stock_count,
        business_health_score=health_score,
    )


@router.get("/profit", response_model=ProfitAnalyticsOut)
def profit_analytics(days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    sales = db.query(Sale).filter(Sale.business_id == current_user.business_id, Sale.sold_at >= cutoff).all()
    revenue = sum((s.total_amount for s in sales), Decimal("0"))
    cost_of_goods = sum((item.quantity * item.product.purchase_price for s in sales for item in s.items), Decimal("0"))
    expenses = db.query(Expense).filter(Expense.business_id == current_user.business_id, Expense.incurred_on >= cutoff.date()).all()
    total_expenses = sum((e.amount for e in expenses), Decimal("0"))
    estimated_profit = revenue - cost_of_goods - total_expenses

    return ProfitAnalyticsOut(
        revenue=revenue,
        cost_of_goods=cost_of_goods,
        expenses=total_expenses,
        estimated_profit=estimated_profit,
    )
