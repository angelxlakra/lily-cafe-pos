from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class DailyCashCounter(Base):
    __tablename__ = "daily_cash_counter"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    opening_balance = Column(Numeric(10, 2), nullable=False)
    closing_balance = Column(Numeric(10, 2), nullable=True)
    expected_closing = Column(Numeric(10, 2), nullable=True)
    variance = Column(Numeric(10, 2), nullable=True)  # actual - expected
    notes = Column(String(500), nullable=True)
    opened_by = Column(String(100), nullable=False)
    closed_by = Column(String(100), nullable=True)
    verified_by = Column(String(100), nullable=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False, index=True)

    @property
    def status(self) -> str:
        if self.is_verified:
            return "verified"
        elif self.closing_balance is not None:
            return "closed_pending_verification"
        else:
            return "open"
