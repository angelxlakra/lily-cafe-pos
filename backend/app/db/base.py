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
from app.models.settings_model import AppSetting  # noqa
from app.models.oauth_models import (  # noqa
    OAuthAuthorizationCode,
    OAuthClient,
    OAuthGrantToken,
    OAuthPendingAuthorization,
)

from app.models.costing_models import ( DishCosting, DishCostingIngredient)

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
    "AppSetting",
    "DishCosting", # Dish Costing
    "DishCostingIngredient", # Dish Costing
    "OAuthClient",
    "OAuthPendingAuthorization",
    "OAuthAuthorizationCode",
    "OAuthGrantToken",
]
