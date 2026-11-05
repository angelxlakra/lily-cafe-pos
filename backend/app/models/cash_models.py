from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

# Every row the drawer is counted in: column suffix → rupee value. Notes first,
# then coins. ₹20 and ₹10 coins have their own rows, apart from the notes.
DENOMINATIONS = {
    "500s": 500, "200s": 200, "100s": 100, "50s": 50, "20s": 20, "10s": 10,
    "coin_20s": 20, "coin_10s": 10, "5s": 5, "2s": 2, "1s": 1,
}


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

    # v0.2 Patch - Denomination counting for opening balance
    opening_500s = Column(Integer, nullable=False, default=0)
    opening_200s = Column(Integer, nullable=False, default=0)
    opening_100s = Column(Integer, nullable=False, default=0)
    opening_50s = Column(Integer, nullable=False, default=0)
    opening_20s = Column(Integer, nullable=False, default=0)
    opening_10s = Column(Integer, nullable=False, default=0)
    opening_coin_20s = Column(Integer, nullable=False, default=0)
    opening_coin_10s = Column(Integer, nullable=False, default=0)
    opening_5s = Column(Integer, nullable=False, default=0)
    opening_2s = Column(Integer, nullable=False, default=0)
    opening_1s = Column(Integer, nullable=False, default=0)

    # v0.2 Patch - Denomination counting for closing balance
    closing_500s = Column(Integer, nullable=True)
    closing_200s = Column(Integer, nullable=True)
    closing_100s = Column(Integer, nullable=True)
    closing_50s = Column(Integer, nullable=True)
    closing_20s = Column(Integer, nullable=True)
    closing_10s = Column(Integer, nullable=True)
    closing_coin_20s = Column(Integer, nullable=True)
    closing_coin_10s = Column(Integer, nullable=True)
    closing_5s = Column(Integer, nullable=True)
    closing_2s = Column(Integer, nullable=True)
    closing_1s = Column(Integer, nullable=True)

    @property
    def status(self) -> str:
        if self.is_verified:
            return "verified"
        elif self.closing_balance is not None:
            return "closed_pending_verification"
        else:
            return "open"
