from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, DateTime, Date, Enum
from decimal import Decimal

from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import enum
from app.db.session import Base


PRESENCE = "presence"


def presence_quantity(value) -> Decimal:
    """A yes/no item holds exactly 1 (have it) or 0 (out)."""
    return Decimal(1) if value > 0 else Decimal(0)

class InventoryCategory(Base):
    __tablename__ = "inventory_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    # Owner-set position in the nightly count (ties fall back to id, i.e.
    # the order the WhatsApp checklist was imported in).
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    items = relationship("InventoryItem", back_populates="category")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    unit = Column(String(20), nullable=False)  # "L", "kg", "pcs", "g", "ml"
    current_quantity = Column(Numeric(10, 2), nullable=False, default=0)
    min_threshold = Column(Numeric(10, 2), nullable=False, default=0)
    cost_per_unit = Column(Numeric(10, 2), nullable=True)
    category_id = Column(Integer, ForeignKey("inventory_categories.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    # "number" (counted with a quantity) or "presence" (answered yes/no).
    count_mode = Column(String(10), nullable=False, default="number", server_default="number")
    # Optional bridge from the count unit to a recipe unit: 1 bottle holds 700 ml.
    pack_size = Column(Numeric(10, 3), nullable=True)
    pack_unit = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("InventoryCategory", back_populates="items")
    transactions = relationship("InventoryTransaction", back_populates="item")
    costing_ingredients = relationship("DishCostingIngredient", back_populates="inventory_item")

    @validates("current_quantity", "count_mode")
    def _clamp_presence(self, key, value):
        """Keep a yes/no item at 1 or 0 whoever writes it.

        Lives on the model because five paths write current_quantity (count,
        purchase, usage, adjustment, the setup grid); "record usage: 3" on
        chilli oil must land on 0, not -3.
        """
        if key == "count_mode":
            # Also covers InventoryItem(current_quantity=5, count_mode="presence"),
            # where the quantity may be set before the mode.
            if value == PRESENCE and self.current_quantity is not None:
                self.current_quantity = presence_quantity(self.current_quantity)
            return value
        if self.count_mode == PRESENCE and value is not None:
            return presence_quantity(value)
        return value

    @property
    def is_presence(self) -> bool:
        return self.count_mode == PRESENCE

    @property
    def is_low_stock(self) -> bool:
        return self.current_quantity < self.min_threshold

class Vendor(Base):
    """Who a purchase was bought from. Deliberately minimal: a purchase never
    waits on vendor setup, so vendor_id on a transaction stays optional."""
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    USAGE = "USAGE"
    ADJUSTMENT = "ADJUSTMENT"

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False, index=True) # Storing enum as string for simplicity in SQLite
    quantity = Column(Numeric(10, 2), nullable=False)  # Positive or negative
    notes = Column(String(500), nullable=True)
    recorded_by = Column(String(100), nullable=False)  # Username/staff name
    previous_quantity = Column(Numeric(10, 2), nullable=False)
    new_quantity = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    # What was paid for this line, in rupees. PURCHASE rows only; NULL when not
    # entered. 0 is a gift. Unit price is total_amount / quantity, never stored.
    total_amount = Column(Numeric(10, 2), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True, index=True)

    # Relationships
    item = relationship("InventoryItem", back_populates="transactions")
    vendor = relationship("Vendor")


class CountLineStatus(str, enum.Enum):
    CHECKED = "checked"   # counted and matched the system quantity
    CHANGED = "changed"   # counted and differed; stock was adjusted
    SKIPPED = "skipped"   # not counted this time


class InventoryCount(Base):
    """One saved nightly stock count: who counted, when, and how it went."""
    __tablename__ = "inventory_counts"

    id = Column(Integer, primary_key=True, index=True)
    business_date = Column(Date, nullable=False, index=True)
    counted_by = Column(String(100), nullable=False)
    items_total = Column(Integer, nullable=False)
    items_checked = Column(Integer, nullable=False)
    items_changed = Column(Integer, nullable=False)
    items_skipped = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    lines = relationship("InventoryCountLine", back_populates="count", cascade="all, delete-orphan")


class InventoryCountLine(Base):
    """Per-item outcome of a count, so "checked, correct" differs from "skipped"."""
    __tablename__ = "inventory_count_lines"

    id = Column(Integer, primary_key=True, index=True)
    count_id = Column(Integer, ForeignKey("inventory_counts.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    status = Column(String(10), nullable=False)
    previous_quantity = Column(Numeric(10, 2), nullable=False)
    counted_quantity = Column(Numeric(10, 2), nullable=True)

    count = relationship("InventoryCount", back_populates="lines")
    item = relationship("InventoryItem")
