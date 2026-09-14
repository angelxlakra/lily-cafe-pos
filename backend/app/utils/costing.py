"""Pure dish-costing math. No I/O, no DB."""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from app.core import settings_store
from app.models.costing_models import OVERHEAD_KINDS
from app.utils.units import convert

MONEY = Decimal("0.01")
PERCENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def pct(value) -> Decimal:
    return Decimal(value).quantize(PERCENT, rounding=ROUND_HALF_UP)


@dataclass
class IngredientInput:
    item_id: int
    name: str
    quantity: Decimal
    unit: str
    stock_unit: str
    cost_per_unit: Decimal | None
    is_active: bool = True


@dataclass
class OverheadInput:
    mode: str
    value: Decimal
    inherited: bool


@dataclass
class IngredientLine:
    item_id: int
    name: str
    quantity: Decimal
    unit: str
    stock_unit: str
    unit_price: Decimal
    line_cost: Decimal
    share_percent: Decimal | None
    price_missing: bool
    is_active: bool


@dataclass
class OverheadLine:
    kind: str
    mode: str
    value: Decimal
    amount: Decimal
    percent: Decimal | None
    inherited: bool


@dataclass
class CostBreakdown:
    ingredients: list[IngredientLine]
    overheads: list[OverheadLine]
    raw_material_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    yield_units: Decimal
    raw_cost_per_unit: Decimal
    cost_per_unit: Decimal
    selling_price: Decimal | None
    margin_amount: Decimal | None
    margin_percent: Decimal | None
    food_cost_percent: Decimal | None
    target_margin_percent: Decimal | None
    suggested_price: Decimal | None
    is_complete: bool = True
    warnings: list[str] = field(default_factory=list)


def compute(
    ingredients: list[IngredientInput],
    overheads: dict[str, OverheadInput],
    yield_units,
    selling_price=None,
    target_margin_percent=None,
) -> CostBreakdown:
    if Decimal(yield_units) <= 0:
        raise ValueError("Yield must be greater than zero")

    warnings: list[str] = []
    lines: list[IngredientLine] = []
    raw = Decimal("0")

    for ing in ingredients:
        price_missing = ing.cost_per_unit is None
        price = Decimal("0") if price_missing else Decimal(ing.cost_per_unit)
        qty_in_stock_unit = convert(ing.quantity, ing.unit, ing.stock_unit)
        line_cost = money(qty_in_stock_unit * price)
        raw += line_cost

        if price_missing:
            warnings.append(f"No price on record for {ing.name} - counted as 0")
        if not ing.is_active:
            warnings.append(f"{ing.name} is no longer an active inventory item")

        lines.append(
            IngredientLine(
                item_id=ing.item_id,
                name=ing.name,
                quantity=Decimal(ing.quantity),
                unit=ing.unit,
                stock_unit=ing.stock_unit,
                unit_price=money(price),
                line_cost=line_cost,
                share_percent=None,
                price_missing=price_missing,
                is_active=ing.is_active,
            )
        )

    for line in lines:
        line.share_percent = pct(line.line_cost / raw * 100) if raw > 0 else None

    overhead_lines: list[OverheadLine] = []
    overhead_cost = Decimal("0")
    for kind in OVERHEAD_KINDS:
        cfg = overheads[kind]
        if cfg.mode == "percent":
            amount = money(raw * Decimal(cfg.value) / 100)
            percent = pct(cfg.value)
        elif cfg.mode == "amount":
            amount = money(cfg.value)
            percent = pct(amount / raw * 100) if raw > 0 else None
        else:
            raise ValueError(f"Unknown overhead mode: {cfg.mode!r}")
        overhead_cost += amount
        overhead_lines.append(
            OverheadLine(
                kind=kind,
                mode=cfg.mode,
                value=Decimal(cfg.value),
                amount=amount,
                percent=percent,
                inherited=cfg.inherited,
            )
        )

    total_cost = raw + overhead_cost
    units = Decimal(yield_units)
    cost_per_unit = money(total_cost / units)
    raw_cost_per_unit = money(raw / units)

    margin_amount = margin_percent = food_cost_percent = None
    sp = None
    if selling_price is not None and Decimal(selling_price) > 0:
        sp = Decimal(selling_price)
        margin_amount = money(sp - cost_per_unit)
        margin_percent = pct((sp - cost_per_unit) / sp * 100)
        food_cost_percent = pct(raw_cost_per_unit / sp * 100)
        if margin_amount < 0:
            warnings.append("Selling price is below cost")

    suggested_price = None
    target = None
    if target_margin_percent is not None:
        target = Decimal(target_margin_percent)
        if target >= 100:
            raise ValueError("Target margin must be below 100%")
        suggested_price = money(cost_per_unit / (1 - target / 100))

    return CostBreakdown(
        ingredients=lines,
        overheads=overhead_lines,
        raw_material_cost=money(raw),
        overhead_cost=money(overhead_cost),
        total_cost=money(total_cost),
        yield_units=units,
        raw_cost_per_unit=raw_cost_per_unit,
        cost_per_unit=cost_per_unit,
        selling_price=sp,
        margin_amount=margin_amount,
        margin_percent=margin_percent,
        food_cost_percent=food_cost_percent,
        target_margin_percent=target,
        suggested_price=suggested_price,
        is_complete=not any(line.price_missing for line in lines),
        warnings=warnings,
    )


def resolve_overheads(costing=None) -> dict[str, OverheadInput]:
    resolved: dict[str, OverheadInput] = {}
    for kind in OVERHEAD_KINDS:
        mode = getattr(costing, f"{kind}_mode", None) if costing else None
        value = getattr(costing, f"{kind}_value", None) if costing else None

        if mode is None or value is None:
            mode = settings_store.get(f"costing.{kind}.mode", "percent")
            value = Decimal(settings_store.get(f"costing.{kind}.value", "0"))
            inherited = True
        else:
            value = Decimal(value)
            inherited = False

        resolved[kind] = OverheadInput(mode=mode, value=value, inherited=inherited)
    return resolved


def resolve_target_margin(costing=None) -> Decimal:
    if costing is not None and costing.target_margin_percent is not None:
        return Decimal(costing.target_margin_percent)
    return Decimal(settings_store.get("costing.target_margin_percent", "65"))


def to_inputs(costing, price_overrides: dict[int, Decimal] | None = None) -> list[IngredientInput]:
    overrides = price_overrides or {}
    inputs = []
    for row in costing.ingredients:
        item = row.inventory_item
        price = overrides.get(item.id, item.cost_per_unit)
        inputs.append(
            IngredientInput(
                item_id=item.id,
                name=item.name,
                quantity=Decimal(row.quantity),
                unit=row.unit,
                stock_unit=item.unit,
                cost_per_unit=Decimal(price) if price is not None else None,
                is_active=item.is_active,
            )
        )
    return inputs
