"""Fill a local database with several weeks of believable orders.

For demos and for exercising the analytics and Ask screens against data that
has shape — busy evenings, quiet Mondays, a few cancellations, some parcels.
Runs the menu seed first if the menu is empty. Refuses to add orders to a
database that already has some, unless --force.

    DATABASE_URL=sqlite:///./restaurant.db uv run python -m scripts.seed_demo_orders
"""

import random
import sys
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

from app.db.session import SessionLocal, init_db
from app.models.cash_models import DailyCashCounter
from app.models.inventory_models import (
    InventoryCategory,
    InventoryItem,
    InventoryTransaction,
    TransactionType,
)
from app.models.models import (
    Category,
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentMethod,
)

IST = timezone(timedelta(hours=5, minutes=30))
WEEKS = 8
GST_RATE = Decimal("0.05")

# Relative footfall by weekday (Mon=0) and by hour: cafes are quiet on Monday
# and busiest at breakfast and evening.
WEEKDAY_WEIGHT = [0.6, 0.8, 0.85, 0.9, 1.0, 1.4, 1.3]
HOUR_WEIGHT = {8: 0.6, 9: 1.0, 10: 0.9, 11: 0.6, 12: 0.8, 13: 0.9, 14: 0.5,
               15: 0.4, 16: 0.7, 17: 1.1, 18: 1.3, 19: 1.2, 20: 0.9, 21: 0.5}
PAYMENT_MIX = [PaymentMethod.UPI] * 6 + [PaymentMethod.CASH] * 3 + [PaymentMethod.CARD]


def main(argv: list[str]) -> int:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            from scripts.seed_data import seed_database

            seed_database()

        if db.query(Order).count() and "--force" not in argv:
            print("Orders already exist; pass --force to add more.")
            return 1

        menu = db.query(MenuItem).filter(MenuItem.is_available.is_(True)).all()
        if not menu:
            print("No menu items to order from.")
            return 1

        rng = random.Random(42)
        # Popularity is skewed so 'top items' has a clear answer.
        weights = [max(1, int(rng.paretovariate(1.2))) for _ in menu]

        today = datetime.now(IST).date()
        start = today - timedelta(days=WEEKS * 7)
        created = 0
        day = start
        counter = 1
        while day <= today:
            base = 22 * WEEKDAY_WEIGHT[day.weekday()]
            for hour, hw in HOUR_WEIGHT.items():
                for _ in range(int(rng.gauss(base * hw / 10, 0.8)) if base * hw / 10 > 0 else 0):
                    at = datetime(day.year, day.month, day.day, hour, rng.randrange(60), tzinfo=IST)
                    if at > datetime.now(IST):
                        continue
                    _order(db, rng, menu, weights, at.astimezone(UTC).replace(tzinfo=None), counter)
                    counter += 1
                    created += 1
            db.flush()
            day += timedelta(days=1)

        _inventory(db, rng, start, today)
        _cash_counters(db, rng, start, today)
        db.commit()
        print(f"Created {created} orders over {WEEKS} weeks ending {today:%d %b %Y}.")
        return 0
    finally:
        db.close()


def _order(db, rng, menu, weights, created_at, n):
    items = rng.choices(menu, weights=weights, k=rng.choice([1, 1, 2, 2, 3]))
    is_parcel = rng.random() < 0.25
    subtotal = 0
    order = Order(
        order_number=f"D{created_at:%y%m%d}-{n:05d}",
        table_number=rng.randint(1, 10),
        subtotal=0, gst_amount=0, total_amount=0,
        status=OrderStatus.PAID, created_at=created_at, updated_at=created_at,
    )
    db.add(order)
    db.flush()
    for item in items:
        qty = rng.choice([1, 1, 1, 2, 2, 3])
        line = item.price * qty
        subtotal += line
        db.add(OrderItem(
            order_id=order.id, menu_item_id=item.id, menu_item_name=item.name,
            quantity=qty, quantity_served=qty, unit_price=item.price, subtotal=line,
            is_beverage=item.is_beverage, is_served=True, is_parcel=is_parcel,
        ))
    gst = int(Decimal(subtotal) * GST_RATE)
    order.subtotal, order.gst_amount, order.total_amount = subtotal, gst, subtotal + gst

    if rng.random() < 0.04:
        order.status = OrderStatus.CANCELED
        order.canceled_at = created_at + timedelta(minutes=5)
        order.canceled_by = "admin"
        order.cancel_reason = rng.choice(["Customer left", "Wrong order", "Duplicate"])
        return

    method = rng.choice(PAYMENT_MIX)
    if rng.random() < 0.08 and order.total_amount > 20000:
        half = order.total_amount // 2
        db.add(Payment(order_id=order.id, payment_method=PaymentMethod.CASH, amount=half, created_at=created_at))
        db.add(Payment(order_id=order.id, payment_method=PaymentMethod.UPI, amount=order.total_amount - half, created_at=created_at))
    else:
        db.add(Payment(order_id=order.id, payment_method=method, amount=order.total_amount, created_at=created_at))


def _inventory(db, rng, start, today):
    if db.query(InventoryItem).count():
        return
    cat = InventoryCategory(name="Kitchen", created_at=datetime.now(), updated_at=datetime.now())
    db.add(cat)
    db.flush()
    stock = [
        ("Milk", "litre", 40, 15, "62"), ("Tea leaves", "kg", 6, 2, "480"),
        ("Coffee beans", "kg", 3, 2, "900"), ("Sugar", "kg", 18, 5, "44"),
        ("Paneer", "kg", 4, 3, "380"), ("Rice", "kg", 25, 10, "68"),
        ("Cooking oil", "litre", 9, 5, "140"), ("Butter", "kg", 2, 2, "520"),
    ]
    for name, unit, qty, threshold, cost in stock:
        item = InventoryItem(name=name, unit=unit, current_quantity=Decimal(qty),
                             min_threshold=Decimal(threshold), cost_per_unit=Decimal(cost), category_id=cat.id)
        db.add(item)
        db.flush()
        day = start
        while day <= today:
            at = datetime(day.year, day.month, day.day, 22, tzinfo=IST).astimezone(UTC).replace(tzinfo=None)
            used = Decimal(rng.randint(1, 4)) if unit != "kg" else Decimal(rng.random()).quantize(Decimal("0.1"))
            db.add(InventoryTransaction(item_id=item.id, transaction_type=TransactionType.USAGE, quantity=-used,
                                        recorded_by="admin", previous_quantity=item.current_quantity + used,
                                        new_quantity=item.current_quantity, created_at=at))
            if day.weekday() == 0:
                bought = used * 7
                db.add(InventoryTransaction(item_id=item.id, transaction_type=TransactionType.PURCHASE, quantity=bought,
                                            recorded_by="admin", previous_quantity=item.current_quantity,
                                            new_quantity=item.current_quantity + bought, created_at=at))
            day += timedelta(days=1)


def _cash_counters(db, rng, start, today):
    if db.query(DailyCashCounter).count():
        return
    day = start
    while day <= today:
        opening = Decimal(rng.choice([2000, 2500, 3000]))
        expected = opening + Decimal(rng.randint(3000, 9000))
        variance = Decimal(rng.choice([0, 0, 0, -50, 20, -100]))
        db.add(DailyCashCounter(
            date=day, opening_balance=opening, closing_balance=expected + variance,
            expected_closing=expected, variance=variance, opened_by="admin", closed_by="admin",
            is_verified=day < today, verified_by="owner" if day < today else None,
        ))
        day += timedelta(days=1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
