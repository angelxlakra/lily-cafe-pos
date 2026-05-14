# backend/app/utils/print_queue.py
"""Builds print job payloads and enqueues them for the relay agent."""

import json
from sqlalchemy.orm import Session
from app.models.models import Order, OrderItem
from app.models.print_job import PrintJob


def _build_payload(order: Order, items: list[OrderItem], station: str) -> str:
    """Serialise everything the agent needs to print a chit."""
    return json.dumps({
        "order_number": order.order_number,
        "table_number": order.table_number,
        "customer_name": order.customer_name,
        "created_at": order.created_at.isoformat(),
        "station": station,
        "items": [
            {
                "name": item.menu_item_name,
                "quantity": item.quantity,
                "is_beverage": item.is_beverage,
                "is_parcel": item.is_parcel,
            }
            for item in items
        ],
    })


def enqueue_chit_jobs(db: Session, order: Order, new_items: list[OrderItem]) -> int:
    """
    Create PrintJob rows for each station that has items.
    Returns the number of jobs created.
    Called from the orders endpoint instead of print_order_chit().
    """
    kitchen = [i for i in new_items if not i.is_parcel and not i.is_beverage]
    bar = [i for i in new_items if not i.is_parcel and i.is_beverage]
    parcel = [i for i in new_items if i.is_parcel]

    count = 0
    for station, items in [("kitchen", kitchen), ("bar", bar), ("parcel", parcel)]:
        if not items:
            continue
        job = PrintJob(
            order_id=order.id,
            station=station,
            status="pending",
            payload=_build_payload(order, items, station),
        )
        db.add(job)
        count += 1

    db.commit()
    return count
