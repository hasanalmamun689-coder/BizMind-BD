from decimal import Decimal
from pydantic import BaseModel


class DashboardSummaryOut(BaseModel):
    total_sales: Decimal
    total_profit_estimate: Decimal
    inventory_value: Decimal
    low_stock_count: int
    business_health_score: int


class ProfitAnalyticsOut(BaseModel):
    revenue: Decimal
    cost_of_goods: Decimal
    expenses: Decimal
    estimated_profit: Decimal
