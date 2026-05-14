"""PrintJob model — queue table for the print relay agent."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.session import Base


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    station = Column(String(20), nullable=False)          # "kitchen" | "bar" | "parcel"
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending | printing | done | failed
    payload = Column(Text, nullable=False)                # JSON: all data the agent needs to print
    attempts = Column(Integer, default=0, nullable=False)
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)
