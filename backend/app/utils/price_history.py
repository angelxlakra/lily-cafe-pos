"""The history of each dish's numbers: a row only when something changed.

`record()` re-costs every recipe and compares it with that recipe's latest row, so a hook
only says what just happened (a purchase, a price edit, a recipe save). It never has to
know which dishes that touched: a spice price reaches Cajun masala and every dish using
it, and each gets its own row. What moved is worked out on read, by `moves()`.

ponytail: this re-costs every recipe on each call. Fine at ~100 dishes; narrow it to the
dishes behind a changed item (costing._passes_through) if it ever gets slow.
"""

import json
import logging
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.costing_models import DishCosting, DishPriceHistory

logger = logging.getLogger(__name__)

CAUSES = ("recipe", "menu_price", "purchase", "typed_price", "default_charges", "baseline")


def _d(value) -> str:
    return format(Decimal(value).quantize(Decimal("0.0001")), "f")


def _snapshot(b) -> dict:
    """Everything worth keeping about a costed recipe, as plain JSON."""
    return {
        "price": None if b.selling_price is None else _d(b.selling_price),
        "cost": _d(b.cost_per_unit),
        "raw": _d(b.raw_material_cost),
        "margin": None if b.margin_percent is None else _d(b.margin_percent),
        "yield": _d(b.yield_units),
        "target": None if b.target_margin_percent is None else _d(b.target_margin_percent),
        "complete": b.is_complete,
        "charges": [
            {"kind": o.kind, "mode": o.mode, "value": _d(o.value), "amount": _d(o.amount), "inherited": o.inherited}
            for o in b.overheads
        ],
        "recipe": [
            {
                "item_id": i.item_id, "name": i.name, "quantity": _d(i.quantity), "unit": i.unit,
                "stock_unit": i.stock_unit, "unit_price": _d(i.unit_price), "line_cost": _d(i.line_cost),
            }
            for i in b.ingredients
        ],
    }


def _fingerprint(snap: dict) -> str:
    """The snapshot without names or where a charge came from: what counts as a change."""
    core = {
        **snap,
        "charges": [{k: v for k, v in c.items() if k != "inherited"} for c in snap["charges"]],
        "recipe": [{k: v for k, v in r.items() if k != "name"} for r in snap["recipe"]],
    }
    return json.dumps(core, sort_keys=True)


def record(db: Session, cause: str, actor: str | None, detail: str | None = None,
           note: str | None = None, note_for: tuple[str, int] | None = None) -> int:
    """Add a row for every recipe whose numbers differ from its latest row; returns how many.

    `note_for` is ("menu", id) or ("made", id): that recipe gets a row (and the note) even if
    nothing moved. Never raises: a failure here must not undo the change that called it.
    """
    try:
        return _record(db, cause, actor, detail, note, note_for)
    except Exception:
        logger.exception("price history: could not record %s", cause)
        db.rollback()
        return 0


def _record(db, cause, actor, detail, note, note_for) -> int:
    # Imported here: the costing endpoints import this module's callers.
    from fastapi import HTTPException
    from app.api.v1.endpoints.costing import _compute_breakdown

    latest_ids = [i for (i,) in db.query(func.max(DishPriceHistory.id)).group_by(
        DishPriceHistory.menu_item_id, DishPriceHistory.inventory_item_id).all()]
    latest = {}
    for row in db.query(DishPriceHistory).filter(DishPriceHistory.id.in_(latest_ids)).all():
        latest[("menu", row.menu_item_id) if row.menu_item_id else ("made", row.inventory_item_id)] = row

    memo: dict = {}
    added = 0
    for costing in db.query(DishCosting).all():
        menu_item, made = costing.menu_item, costing.made_item
        if menu_item is None and (made is None or not made.is_active):
            continue
        key = ("menu", costing.menu_item_id) if menu_item else ("made", costing.inventory_item_id)
        try:
            b = _compute_breakdown(costing, menu_item, memo=memo)
        except HTTPException:
            continue  # a recipe that can't be costed has no numbers to keep
        snap = _snapshot(b)
        fp = _fingerprint(snap)
        previous = latest.get(key)
        wants_note = bool(note) and note_for == key
        if previous is not None and previous.fingerprint == fp and not wants_note:
            continue
        db.add(DishPriceHistory(
            menu_item_id=costing.menu_item_id, inventory_item_id=costing.inventory_item_id,
            name=(menu_item or made).name, cause=cause, detail=(detail or None) and detail[:300],
            note=note if wants_note else None, actor=actor,
            menu_price=b.selling_price, cost_per_unit=b.cost_per_unit, raw_cost=b.raw_material_cost,
            margin_percent=b.margin_percent, yield_units=b.yield_units,
            target_margin_percent=b.target_margin_percent, is_complete=b.is_complete,
            data=json.dumps(snap), fingerprint=fp,
        ))
        added += 1
    if added:
        db.commit()
    return added


# Reading

def _inr(value) -> str:
    return f"₹{Decimal(value):,.2f}"


def _charge_text(c: dict) -> str:
    v = Decimal(c["value"]).normalize()
    v = format(v, "f")
    return {"percent": f"{v}%", "amount": f"₹{v} per batch", "each": f"₹{v} per portion"}.get(c["mode"], v)


def moves(before: dict | None, after: dict) -> list[str]:
    """What moved between two snapshots, in the owners' words."""
    if before is None:
        return []
    out = []
    if before["price"] != after["price"]:
        out.append(f"Menu price {_inr(before['price']) if before['price'] else 'none'} → "
                   f"{_inr(after['price']) if after['price'] else 'none'}")
    old = {r["item_id"]: r for r in before["recipe"]}
    new = {r["item_id"]: r for r in after["recipe"]}
    for item_id, r in new.items():
        o = old.get(item_id)
        if o is None:
            out.append(f"Added {r['name']} ({Decimal(r['quantity']).normalize():f} {r['unit']})")
            continue
        if (o["quantity"], o["unit"]) != (r["quantity"], r["unit"]):
            out.append(f"{r['name']} {Decimal(o['quantity']).normalize():f} {o['unit']} → "
                       f"{Decimal(r['quantity']).normalize():f} {r['unit']}")
        if o["unit_price"] != r["unit_price"]:
            out.append(f"{r['name']} {_inr(o['unit_price'])} → {_inr(r['unit_price'])}/{r['stock_unit']}")
    out += [f"Removed {r['name']}" for item_id, r in old.items() if item_id not in new]
    if before["yield"] != after["yield"]:
        out.append(f"Batch size {Decimal(before['yield']).normalize():f} → {Decimal(after['yield']).normalize():f}")
    old_c = {c["kind"]: c for c in before["charges"]}
    for c in after["charges"]:
        o = old_c.get(c["kind"])
        if o is None or (o["mode"], o["value"]) == (c["mode"], c["value"]):
            if o is not None and o["amount"] != c["amount"]:
                out.append(f"{c['kind'].capitalize()} {_inr(o['amount'])} → {_inr(c['amount'])}")
        else:
            out.append(f"{c['kind'].capitalize()} {_charge_text(o)} → {_charge_text(c)}")
    if before["target"] != after["target"]:
        t = lambda s: f"{Decimal(s).normalize():f}%" if s else "none"
        out.append(f"Target margin {t(before['target'])} → {t(after['target'])}")
    return out
