"""
Import all models here to ensure they are registered with SQLAlchemy Base.
This allows Alembic migrations to detect all models.
"""

from app.db.session import Base  # noqa
from app.models.models import (  # noqa
    Category,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    OrderStatus,
    PaymentMethod,
)
from app.models.inventory_models import (  # noqa
    InventoryCategory,
    InventoryItem,
    InventoryTransaction,
    TransactionType,
)
from app.models.cash_models import DailyCashCounter  # noqa

__all__ = [
    "Base",
    "Category",
    "MenuItem",
    "Order",
    "OrderItem",
    "Payment",
    "OrderStatus",
    "PaymentMethod",
    "InventoryCategory",
    "InventoryItem",
    "InventoryTransaction",
    "TransactionType",
    "DailyCashCounter",
]
