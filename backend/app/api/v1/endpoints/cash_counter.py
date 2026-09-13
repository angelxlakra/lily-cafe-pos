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
from app.api.deps import get_current_user, get_current_owner
from app.core import access
from app.schemas import TokenData

router = APIRouter()


def _require_own_day(current_user: TokenData, day: date, action: str) -> None:
    """
    Admin may only work on the current day's counter; the owner may work on
    any day (e.g. backfilling or correcting an earlier day's count).
    """
    if not access.is_owner(current_user) and day != access.business_today():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Owner login required to {action} for a day other than today.",
        )


def _authorizing_owner(current_user: TokenData) -> str:
    """
    Name to record for an action gated by the owner password.

    When the owner is signed in, that is simply their username. When the
    owner authorizes at the counter while the admin is signed in, record both
    so the trail shows who was operating the till.
    """
    if access.is_owner(current_user):
        return current_user.username
    return f"{settings.OWNER_USERNAME} (via {current_user.username})"[:100]

@router.post("/open", response_model=cash_schemas.DailyCashCounter, status_code=status.HTTP_201_CREATED)
def open_cash_counter(
    data: cash_schemas.DailyCashCounterOpen,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Open the daily cash counter.

    Requires a login, and records who opened it. The admin login may only
    open today's counter; the owner can also open an earlier day.
    """
    _require_own_day(current_user, data.date, "open the cash counter")

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
        opened_by=current_user.username,
    )
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return counter

@router.post("/close", response_model=cash_schemas.DailyCashCounter)
def close_cash_counter(
    data: cash_schemas.DailyCashCounterClose,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Close the daily cash counter.

    Requires a login, and records who closed it. The admin login may only
    close today's counter; the owner can also close an earlier day.
    """
    _require_own_day(current_user, data.date, "close the cash counter")

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
    counter.closed_by = current_user.username
    counter.closed_at = datetime.now()

    db.commit()
    db.refresh(counter)

    # Add computed field for response
    counter_dict = cash_schemas.DailyCashCounter.from_orm(counter)
    counter_dict.cash_payments_total = cash_payments_rupees

    return counter_dict

@router.post("/verify/{counter_id}", response_model=cash_schemas.DailyCashCounter)
def verify_cash_counter(
    counter_id: int,
    verify_data: cash_schemas.DailyCashCounterVerify,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Verify a closed cash counter.

    Authorized by the owner password, so the owner can approve the count at
    the till while the admin is signed in. A login is still required, so the
    action is always attributable to whoever was operating the till.
    """
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
    counter.verified_by = _authorizing_owner(current_user)
    counter.verified_at = datetime.now()
    
    db.commit()
    db.refresh(counter)
    return counter

@router.get("/today", response_model=dict)
def get_today_counter(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get today's cash counter status. Requires a login."""
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
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_owner),
):
    """
    Get cash counter history.

    Owner only — this is a record of previous days' cash, which the admin
    login is not allowed to see.
    """
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

@router.get("/day/{day}")
def get_counter_for_day(
    day: date,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Full cash counter details for a single day (hidden day-lookup page).

    Returns the counter (or null if none was opened that day), the cash
    payments collected, and the nearest earlier/later days that have a
    counter so the UI can step between recorded days.

    The admin login may only look up today; the owner can look up any day.
    """
    _require_own_day(current_user, day, "view the cash counter")

    counter = db.query(DailyCashCounter).filter(DailyCashCounter.date == day).first()

    cash_sum, cash_count = db.query(
        func.sum(Payment.amount), func.count(Payment.id)
    ).filter(
        Payment.payment_method == PaymentMethod.CASH,
        func.date(Payment.created_at) == str(day)
    ).one()
    cash_payments_rupees = Decimal(cash_sum or 0) / 100

    prev_counter = db.query(DailyCashCounter.date).filter(
        DailyCashCounter.date < day
    ).order_by(desc(DailyCashCounter.date)).first()
    next_counter = db.query(DailyCashCounter.date).filter(
        DailyCashCounter.date > day
    ).order_by(DailyCashCounter.date).first()

    counter_data = None
    if counter:
        counter_data = cash_schemas.DailyCashCounter.model_validate(counter).model_dump()
        counter_data['cash_payments_total'] = cash_payments_rupees

    return {
        "date": day,
        "counter": counter_data,
        "cash_payments_total": cash_payments_rupees,
        "cash_payments_count": cash_count or 0,
        "prev_date": prev_counter[0] if prev_counter else None,
        "next_date": next_counter[0] if next_counter else None,
    }

@router.post("/reopen/{counter_id}",response_model=cash_schemas.DailyCashCounter)
def reopen_cash_counter(
    counter_id: int,
    reopen_data: cash_schemas.DailyCashCounterVerify,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Reopen a closed cash counter so the cash can be recounted.

    Authorized by the owner password, like verification, and likewise
    requires a login so the action is attributable.
    """
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
