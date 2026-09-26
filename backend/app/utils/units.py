"""Strict unit conversion for recipe quantities."""

from decimal import Decimal


class IncompatibleUnitError(ValueError):
    """Raised when a unit is unknown or from a different family."""


_UNITS: dict[str, tuple[str, Decimal]] = {
    "g": ("mass", Decimal("1")),
    "kg": ("mass", Decimal("1000")),
    "ml": ("volume", Decimal("1")),
    "l": ("volume", Decimal("1000")),
    "pcs": ("count", Decimal("1")),
}

_ALIASES = {
    "gm": "g",
    "gms": "g",
    "gram": "g",
    "grams": "g",
    "kgs": "kg",
    "kilo": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "mls": "ml",
    "millilitre": "ml",
    "milliliter": "ml",
    "lt": "l",
    "ltr": "l",
    "litre": "l",
    "liter": "l",
    "litres": "l",
    "pc": "pcs",
    "piece": "pcs",
    "pieces": "pcs",
    "no": "pcs",
    "nos": "pcs",
}

SUPPORTED_UNITS = tuple(_UNITS)


def normalize(unit: str) -> str:
    key = (unit or "").strip().lower()
    key = _ALIASES.get(key, key)
    if key not in _UNITS:
        raise IncompatibleUnitError(f"Unknown unit: {unit!r}")
    return key


def family(unit: str) -> str:
    return _UNITS[normalize(unit)][0]


def compatible(from_unit: str, to_unit: str) -> bool:
    try:
        return family(from_unit) == family(to_unit)
    except IncompatibleUnitError:
        return False


def convert(quantity, from_unit: str, to_unit: str) -> Decimal:
    src, dst = normalize(from_unit), normalize(to_unit)
    src_family, src_factor = _UNITS[src]
    dst_family, dst_factor = _UNITS[dst]
    if src_family != dst_family:
        raise IncompatibleUnitError(
            f"Cannot convert {from_unit} to {to_unit} ({src_family} vs {dst_family})"
        )
    return Decimal(quantity) * src_factor / dst_factor
