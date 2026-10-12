from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseBreakdownOut

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Expense).filter(Expense.business_id == current_user.business_id).order_by(Expense.incurred_on.desc()).all()


@router.post("", response_model=ExpenseOut)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = Expense(business_id=current_user.business_id, **payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/breakdown", response_model=list[ExpenseBreakdownOut])
def expense_breakdown(days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(Expense.category, func.sum(Expense.amount).label("total"))
        .filter(Expense.business_id == current_user.business_id, Expense.incurred_on >= cutoff)
        .group_by(Expense.category)
        .all()
    )
    return [ExpenseBreakdownOut(category=r[0], total=r[1] or Decimal("0")) for r in rows]
