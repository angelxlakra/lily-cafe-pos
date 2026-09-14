"""SQLAlchemy models for dish costing sheets."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

OVERHEAD_KINDS = ("packaging", "labour", "fixed", "wastage")


class DishCosting(Base):
    """One costing sheet attached to one menu item."""

    __tablename__ = "dish_costings"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False, unique=True, index=True)
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

    menu_item = relationship("MenuItem")
    ingredients = relationship(
        "DishCostingIngredient",
        back_populates="costing",
        cascade="all, delete-orphan",
        order_by="DishCostingIngredient.sort_order",
    )


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
    inventory_item = relationship("InventoryItem")
