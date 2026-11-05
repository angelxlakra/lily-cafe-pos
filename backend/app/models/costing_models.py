"""SQLAlchemy models for dish costing sheets."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

OVERHEAD_KINDS = ("packaging", "labour", "fixed", "wastage")


class DishCosting(Base):
    """One costing sheet: a menu item's recipe, or the recipe of a kitchen-made inventory item."""

    __tablename__ = "dish_costings"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)
    # Set instead of menu_item_id when this is how a kitchen-made item (a spice mix) is made.
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True, unique=True, index=True)
    yield_units = Column(Numeric(12, 3), nullable=False, default=1)
    target_margin_percent = Column(Numeric(5, 2), nullable=True)
    notes = Column(String(500), nullable=True)

    packaging_mode = Column(String(10), nullable=True)
    packaging_value = Column(Numeric(12, 2), nullable=True)
    labour_mode = Column(String(10), nullable=True)
    labour_value = Column(Numeric(12, 2), nullable=True)
    fixed_mode = Column(String(10), nullable=True)
    fixed_value = Column(Numeric(12, 2), nullable=True)
    wastage_mode = Column(String(10), nullable=True)
    wastage_value = Column(Numeric(12, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    menu_item = relationship("MenuItem", back_populates="costing")
    made_item = relationship("InventoryItem", back_populates="recipe")
    ingredients = relationship("DishCostingIngredient",back_populates="costing",cascade="all, delete-orphan",order_by="DishCostingIngredient.sort_order",)

 
class DishCostingIngredient(Base):
    """One ingredient row in a dish costing sheet."""

    __tablename__ = "dish_costing_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    costing_id = Column(
        Integer,
        ForeignKey("dish_costings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    costing = relationship("DishCosting", back_populates="ingredients")
    inventory_item = relationship("InventoryItem", back_populates="costing_ingredients")


class DishPriceHistory(Base):
    """One moment a dish's (or made item's) numbers changed. Only ever added to.

    No foreign keys on purpose: deleting a recipe or a dish must not delete its past.
    SQLite triggers (ensure_price_history_guard) refuse any UPDATE or DELETE.
    """

    __tablename__ = "dish_price_history"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, nullable=True, index=True)
    inventory_item_id = Column(Integer, nullable=True, index=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # recipe | menu_price | purchase | typed_price | default_charges | baseline
    cause = Column(String(30), nullable=False)
    detail = Column(String(300), nullable=True)
    note = Column(String(300), nullable=True)
    actor = Column(String(100), nullable=True)

    # The numbers a chart needs; everything else is in `data`.
    menu_price = Column(Numeric(12, 2), nullable=True)
    cost_per_unit = Column(Numeric(12, 2), nullable=False)
    raw_cost = Column(Numeric(12, 2), nullable=False)
    margin_percent = Column(Numeric(7, 2), nullable=True)
    yield_units = Column(Numeric(12, 3), nullable=False)
    target_margin_percent = Column(Numeric(5, 2), nullable=True)
    is_complete = Column(Boolean, nullable=False, default=True)

    # JSON: charges and the recipe copy. `fingerprint` is what "changed" means.
    data = Column(Text, nullable=False)
    fingerprint = Column(Text, nullable=False)
