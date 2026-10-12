from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import AlertSeverity, AlertStatus


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    category = Column(String(50), nullable=False)  # inventory, financial, supplier, sales, ai
    severity = Column(Enum(AlertSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    related_entity = Column(String(120), nullable=True)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.OPEN)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
