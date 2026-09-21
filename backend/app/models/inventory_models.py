from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, DateTime, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("InventoryCategory", back_populates="items")
    transactions = relationship("InventoryTransaction", back_populates="item")
    
    @property
    def is_low_stock(self) -> bool:
        return self.current_quantity < self.min_threshold

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
    
    # Relationships
    item = relationship("InventoryItem", back_populates="transactions")


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
