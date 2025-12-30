from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class DailyCashCounterBase(BaseModel):
    date: date
    notes: Optional[str] = Field(None, max_length=500)

class DailyCashCounterOpen(DailyCashCounterBase):
    opening_balance: Decimal = Field(..., ge=0)

class DailyCashCounterClose(BaseModel):
    date: date
    closing_balance: Decimal = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=500)

class DailyCashCounterVerify(BaseModel):
    owner_password: str

class DailyCashCounter(DailyCashCounterBase):
    id: int
    opening_balance: Decimal
    closing_balance: Optional[Decimal] = None
    expected_closing: Optional[Decimal] = None
    variance: Optional[Decimal] = None
    opened_by: str
    closed_by: Optional[str] = None
    verified_by: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    is_verified: bool
    status: str # Computed property
    cash_payments_total: Optional[Decimal] = None # Computed for response

    class Config:
        from_attributes = True  # Pydantic v2 syntax (was orm_mode in v1)

class CashCounterSummary(BaseModel):
    total_variance: Decimal
    average_variance: Decimal
    unverified_count: int

class CashCounterHistory(BaseModel):
    counters: list[DailyCashCounter]
    total: int
    limit: int
    offset: int
    summary: CashCounterSummary
