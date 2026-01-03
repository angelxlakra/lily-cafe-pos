from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime
from decimal import Decimal
import os

from app.db.session import get_db
from app.models.cash_models import DailyCashCounter
from app.models.models import Payment, PaymentMethod
from app.schemas import cash_schemas
from app.core.config import settings
from app.core.security import verify_password

router = APIRouter()

@router.post("/open", response_model=cash_schemas.DailyCashCounter, status_code=status.HTTP_201_CREATED)
def open_cash_counter(data: cash_schemas.DailyCashCounterOpen, db: Session = Depends(get_db)):
    """Open the daily cash counter."""
    # Check if already open
    existing = db.query(DailyCashCounter).filter(DailyCashCounter.date == data.date).first()
    if existing:
        raise HTTPException(status_code=400, detail="Counter already open for this date")

    if data.date > date.today():
        raise HTTPException(status_code=400, detail="Date cannot be in the future")

    # v0.2 Patch - Calculate opening_balance from denomination counts
    opening_balance = Decimal(
        data.opening_500s * 500 +
        data.opening_200s * 200 +
        data.opening_100s * 100 +
        data.opening_50s * 50 +
        data.opening_20s * 20 +
        data.opening_10s * 10
    )

    counter = DailyCashCounter(
        date=data.date,
        opening_balance=opening_balance,
        opening_500s=data.opening_500s,
        opening_200s=data.opening_200s,
        opening_100s=data.opening_100s,
        opening_50s=data.opening_50s,
        opening_20s=data.opening_20s,
        opening_10s=data.opening_10s,
        notes=data.notes,
        opened_by="admin" # TODO: Get from auth
    )
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return counter

@router.post("/close", response_model=cash_schemas.DailyCashCounter)
def close_cash_counter(data: cash_schemas.DailyCashCounterClose, db: Session = Depends(get_db)):
    """Close the daily cash counter."""
    counter = db.query(DailyCashCounter).filter(DailyCashCounter.date == data.date).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found for this date")

    if counter.closing_balance is not None:
        raise HTTPException(status_code=400, detail="Counter already closed")

    # v0.2 Patch - Calculate closing_balance from denomination counts
    closing_balance = Decimal(
        data.closing_500s * 500 +
        data.closing_200s * 200 +
        data.closing_100s * 100 +
        data.closing_50s * 50 +
        data.closing_20s * 20 +
        data.closing_10s * 10
    )

    # Get total cash payments for the day
    # SQLite specific date filtering
    cash_payments = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_method == PaymentMethod.CASH,
        func.date(Payment.created_at) == str(data.date)
    ).scalar() or 0

    # Payment amount is in paise (integer), convert to decimal rupees
    cash_payments_rupees = Decimal(cash_payments) / 100

    expected_closing = counter.opening_balance + cash_payments_rupees
    variance = closing_balance - expected_closing

    counter.closing_balance = closing_balance
    counter.closing_500s = data.closing_500s
    counter.closing_200s = data.closing_200s
    counter.closing_100s = data.closing_100s
    counter.closing_50s = data.closing_50s
    counter.closing_20s = data.closing_20s
    counter.closing_10s = data.closing_10s
    counter.expected_closing = expected_closing
    counter.variance = variance
    counter.notes = data.notes
    counter.closed_by = "admin" # TODO: Get from auth
    counter.closed_at = datetime.now()

    db.commit()
    db.refresh(counter)

    # Add computed field for response
    counter_dict = cash_schemas.DailyCashCounter.from_orm(counter)
    counter_dict.cash_payments_total = cash_payments_rupees

    return counter_dict

@router.post("/verify/{counter_id}", response_model=cash_schemas.DailyCashCounter)
def verify_cash_counter(counter_id: int, verify_data: cash_schemas.DailyCashCounterVerify, db: Session = Depends(get_db)):
    """Verify cash counter (Owner only)."""
    counter = db.query(DailyCashCounter).filter(DailyCashCounter.id == counter_id).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
        
    if counter.closing_balance is None:
        raise HTTPException(status_code=400, detail="Counter not closed yet")
        
    if counter.is_verified:
        raise HTTPException(status_code=400, detail="Counter already verified")

    # Verify owner password using bcrypt hash
    if not verify_password(verify_data.owner_password, settings.OWNER_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Incorrect owner password")
        
    counter.is_verified = True
    counter.verified_by = "owner"
    counter.verified_at = datetime.now()
    
    db.commit()
    db.refresh(counter)
    return counter

@router.get("/today", response_model=dict)
def get_today_counter(db: Session = Depends(get_db)):
    """Get today's cash counter status."""
    today = date.today()
    counter = db.query(DailyCashCounter).filter(DailyCashCounter.date == today).first()
    
    if counter:
        # Calculate cash payments so far
        cash_payments = db.query(func.sum(Payment.amount)).filter(
            Payment.payment_method == PaymentMethod.CASH,
            func.date(Payment.created_at) == str(today)
        ).scalar() or 0
        cash_payments_rupees = Decimal(cash_payments) / 100

        # Convert ORM model to Pydantic model
        counter_model = cash_schemas.DailyCashCounter.model_validate(counter)

        # Convert to dict and add cash_payments_total
        counter_data = counter_model.model_dump()
        counter_data['cash_payments_total'] = float(cash_payments_rupees)
        return counter_data
    else:
        # Suggest opening balance from yesterday's closing
        yesterday_counter = db.query(DailyCashCounter).order_by(desc(DailyCashCounter.date)).first()
        suggested = 0
        if yesterday_counter and yesterday_counter.closing_balance:
            suggested = yesterday_counter.closing_balance
            
        return {
            "message": "Cash counter not opened for today",
            "date": today,
            "suggested_opening_balance": suggested
        }

@router.get("/history", response_model=cash_schemas.CashCounterHistory)
def get_history(
    limit: int = 30,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get cash counter history."""
    query = db.query(DailyCashCounter)
    total = query.count()
    counters = query.order_by(desc(DailyCashCounter.date)).offset(offset).limit(limit).all()
    
    # Calculate summary stats
    total_variance = 0
    unverified_count = 0
    variance_count = 0
    
    for c in counters:
        if c.variance is not None:
            total_variance += c.variance
            variance_count += 1
        if not c.is_verified and c.closing_balance is not None:
            unverified_count += 1
            
    avg_variance = total_variance / variance_count if variance_count > 0 else 0
    
    return {
        "counters": counters,
        "total": total,
        "limit": limit,
        "offset": offset,
        "summary": {
            "total_variance": total_variance,
            "average_variance": avg_variance,
            "unverified_count": unverified_count
        }
    }

@router.post("/reopen/{counter_id}", response_model=cash_schemas.DailyCashCounter)
def reopen_cash_counter(counter_id: int, reopen_data: cash_schemas.DailyCashCounterVerify, db: Session = Depends(get_db)):
    """Reopen a closed cash counter (Owner only)."""
    counter = db.query(DailyCashCounter).filter(DailyCashCounter.id == counter_id).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")

    # Can only reopen closed counters (not verified ones)
    if counter.status not in ['closed_pending_verification']:
        raise HTTPException(status_code=400, detail="Can only reopen counters pending verification")

    # Verify owner password using bcrypt hash
    if not verify_password(reopen_data.owner_password, settings.OWNER_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Incorrect owner password")

    # Reset counter to "open" state - clear closing data
    counter.closing_balance = None
    counter.closing_500s = None
    counter.closing_200s = None
    counter.closing_100s = None
    counter.closing_50s = None
    counter.closing_20s = None
    counter.closing_10s = None
    counter.expected_closing = None
    counter.variance = None
    counter.closed_by = None
    counter.closed_at = None
    counter.is_verified = False
    counter.verified_by = None
    counter.verified_at = None

    db.commit()
    db.refresh(counter)

    # Calculate cash payments for response
    cash_payments = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_method == PaymentMethod.CASH,
        func.date(Payment.created_at) == str(counter.date)
    ).scalar() or 0
    cash_payments_rupees = Decimal(cash_payments) / 100

    # Convert to dict and add cash_payments_total
    counter_model = cash_schemas.DailyCashCounter.model_validate(counter)
    counter_data = counter_model.model_dump()
    counter_data['cash_payments_total'] = float(cash_payments_rupees)

    return counter_data
