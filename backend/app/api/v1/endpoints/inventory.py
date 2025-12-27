from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from decimal import Decimal

from app.db.session import get_db
from app.models.inventory_models import InventoryCategory, InventoryItem, InventoryTransaction, TransactionType
from app.schemas import inventory_schemas

router = APIRouter()

# ============================================================================
# Categories
# ============================================================================

@router.get("/categories", response_model=List[inventory_schemas.InventoryCategory])
def get_categories(db: Session = Depends(get_db)):
    """Get all inventory categories."""
    return db.query(InventoryCategory).all()

@router.post("/categories", response_model=inventory_schemas.InventoryCategory, status_code=status.HTTP_201_CREATED)
def create_category(category: inventory_schemas.InventoryCategoryCreate, db: Session = Depends(get_db)):
    """Create a new inventory category."""
    db_category = db.query(InventoryCategory).filter(InventoryCategory.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    
    new_category = InventoryCategory(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.patch("/categories/{category_id}", response_model=inventory_schemas.InventoryCategory)
def update_category(category_id: int, category_update: inventory_schemas.InventoryCategoryUpdate, db: Session = Depends(get_db)):
    """Update an inventory category."""
    db_category = db.query(InventoryCategory).filter(InventoryCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category_update.name:
        existing = db.query(InventoryCategory).filter(InventoryCategory.name == category_update.name).first()
        if existing and existing.id != category_id:
            raise HTTPException(status_code=400, detail="Category name already exists")
        db_category.name = category_update.name
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete an inventory category."""
    db_category = db.query(InventoryCategory).filter(InventoryCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has items
    if db_category.items:
        raise HTTPException(status_code=400, detail="Cannot delete category containing items")
    
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}

# ============================================================================
# Items
# ============================================================================

@router.get("/items", response_model=dict)
def get_items(
    category_id: Optional[int] = None,
    is_active: bool = True,
    low_stock: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all inventory items with filtering."""
    query = db.query(InventoryItem)
    
    if is_active:
        query = query.filter(InventoryItem.is_active == True)
    
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)
    
    if search:
        query = query.filter(InventoryItem.name.ilike(f"%{search}%"))
        
    items = query.all()
    
    # Filter low stock in python since it's a property
    if low_stock:
        items = [item for item in items if item.is_low_stock]
        
    # Enrich with category name
    result_items = []
    low_stock_count = 0
    for item in items:
        item_dict = inventory_schemas.InventoryItem.from_orm(item)
        if item.category:
            item_dict.category_name = item.category.name
        item_dict.is_low_stock = item.is_low_stock
        result_items.append(item_dict)
        if item.is_low_stock:
            low_stock_count += 1
            
    return {
        "items": result_items,
        "total": len(result_items),
        "low_stock_count": low_stock_count
    }

@router.get("/items/low-stock", response_model=dict)
def get_low_stock_items(db: Session = Depends(get_db)):
    """Get all low stock items sorted by urgency."""
    items = db.query(InventoryItem).filter(InventoryItem.is_active == True).all()
    low_stock_items = []
    
    for item in items:
        if item.is_low_stock:
            percentage = 0
            if item.min_threshold > 0:
                percentage = (item.current_quantity / item.min_threshold) * 100
            
            item_dict = inventory_schemas.LowStockItem.from_orm(item)
            if item.category:
                item_dict.category_name = item.category.name
            item_dict.percentage_remaining = percentage
            low_stock_items.append(item_dict)
            
    # Sort by percentage remaining (ascending)
    low_stock_items.sort(key=lambda x: x.percentage_remaining)
    
    return {
        "low_stock_items": low_stock_items,
        "count": len(low_stock_items)
    }

@router.get("/items/{item_id}", response_model=inventory_schemas.InventoryItem)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get a single inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_dict = inventory_schemas.InventoryItem.from_orm(item)
    if item.category:
        item_dict.category_name = item.category.name
    item_dict.is_low_stock = item.is_low_stock
    return item_dict

@router.post("/items", response_model=inventory_schemas.InventoryItem, status_code=status.HTTP_201_CREATED)
def create_item(item: inventory_schemas.InventoryItemCreate, db: Session = Depends(get_db)):
    """Create a new inventory item."""
    # Check uniqueness within category if category provided
    if item.category_id:
        existing = db.query(InventoryItem).filter(
            InventoryItem.name == item.name,
            InventoryItem.category_id == item.category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Item name already exists in this category")
            
    new_item = InventoryItem(
        name=item.name,
        unit=item.unit,
        current_quantity=item.current_quantity,
        min_threshold=item.min_threshold,
        cost_per_unit=item.cost_per_unit,
        category_id=item.category_id
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    # Return with computed fields
    item_dict = inventory_schemas.InventoryItem.from_orm(new_item)
    if new_item.category:
        item_dict.category_name = new_item.category.name
    item_dict.is_low_stock = new_item.is_low_stock
    return item_dict

@router.patch("/items/{item_id}", response_model=inventory_schemas.InventoryItem)
def update_item(item_id: int, item_update: inventory_schemas.InventoryItemUpdate, db: Session = Depends(get_db)):
    """Update an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
        
    db.commit()
    db.refresh(item)
    
    item_dict = inventory_schemas.InventoryItem.from_orm(item)
    if item.category:
        item_dict.category_name = item.category.name
    item_dict.is_low_stock = item.is_low_stock
    return item_dict

@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Soft delete an inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.is_active = False
    db.commit()
    return {"message": "Item deactivated successfully"}

# ============================================================================
# Transactions
# ============================================================================

@router.post("/transactions/purchase", status_code=status.HTTP_201_CREATED)
def record_purchase(purchase: inventory_schemas.PurchaseCreate, db: Session = Depends(get_db)):
    """Record a purchase transaction (stock addition)."""
    transactions = []
    
    for item_data in purchase.items:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_data.item_id).first()
        if not item:
            raise HTTPException(status_code=400, detail=f"Item ID {item_data.item_id} not found")
        if not item.is_active:
            raise HTTPException(status_code=400, detail=f"Item {item.name} is inactive")
        if item_data.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
            
        previous_qty = item.current_quantity
        item.current_quantity += item_data.quantity
        new_qty = item.current_quantity
        
        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type=TransactionType.PURCHASE,
            quantity=item_data.quantity,
            notes=item_data.notes,
            recorded_by="admin", # TODO: Get from auth context
            previous_quantity=previous_qty,
            new_quantity=new_qty
        )
        db.add(transaction)
        transactions.append(transaction)
        
    db.commit()
    
    # Refresh to get IDs
    for t in transactions:
        db.refresh(t)
        
    return {
        "message": "Purchase recorded successfully",
        "transactions": [
            {
                "id": t.id,
                "item_id": t.item_id,
                "item_name": t.item.name,
                "transaction_type": t.transaction_type,
                "quantity": t.quantity,
                "previous_quantity": t.previous_quantity,
                "new_quantity": t.new_quantity,
                "recorded_by": t.recorded_by,
                "created_at": t.created_at
            } for t in transactions
        ]
    }

@router.post("/transactions/usage", status_code=status.HTTP_201_CREATED)
def record_usage(usage: inventory_schemas.UsageCreate, db: Session = Depends(get_db)):
    """Record usage transaction (stock reduction)."""
    transactions = []
    warnings = []
    
    for item_data in usage.items:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_data.item_id).first()
        if not item:
            raise HTTPException(status_code=400, detail=f"Item ID {item_data.item_id} not found")
        if item_data.quantity <= 0:
            continue # Skip zero or negative usage
            
        previous_qty = item.current_quantity
        item.current_quantity -= item_data.quantity
        new_qty = item.current_quantity
        
        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type=TransactionType.USAGE,
            quantity=-item_data.quantity, # Negative for usage
            notes=item_data.notes,
            recorded_by=usage.recorded_by,
            previous_quantity=previous_qty,
            new_quantity=new_qty
        )
        db.add(transaction)
        transactions.append(transaction)
        
        if item.is_low_stock:
            warnings.append({
                "item_id": item.id,
                "item_name": item.name,
                "message": f"Now below threshold ({new_qty}/{item.min_threshold})"
            })
            
    db.commit()
    
    for t in transactions:
        db.refresh(t)
        
    return {
        "message": "Usage recorded successfully",
        "transactions": [
            {
                "id": t.id,
                "item_id": t.item_id,
                "item_name": t.item.name,
                "transaction_type": t.transaction_type,
                "quantity": t.quantity,
                "previous_quantity": t.previous_quantity,
                "new_quantity": t.new_quantity,
                "recorded_by": t.recorded_by,
                "created_at": t.created_at
            } for t in transactions
        ],
        "warnings": warnings
    }

@router.post("/transactions/adjustment", status_code=status.HTTP_201_CREATED)
def record_adjustment(adjustment: inventory_schemas.AdjustmentCreate, db: Session = Depends(get_db)):
    """Record inventory adjustment (correction)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == adjustment.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    previous_qty = item.current_quantity
    new_qty = adjustment.new_quantity
    diff = new_qty - previous_qty
    
    item.current_quantity = new_qty
    
    transaction = InventoryTransaction(
        item_id=item.id,
        transaction_type=TransactionType.ADJUSTMENT,
        quantity=diff,
        notes=adjustment.notes,
        recorded_by="admin", # TODO: Get from auth context
        previous_quantity=previous_qty,
        new_quantity=new_qty
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return {
        "id": transaction.id,
        "item_id": transaction.item_id,
        "item_name": item.name,
        "transaction_type": transaction.transaction_type,
        "quantity": transaction.quantity,
        "previous_quantity": transaction.previous_quantity,
        "new_quantity": transaction.new_quantity,
        "recorded_by": transaction.recorded_by,
        "notes": transaction.notes,
        "created_at": transaction.created_at
    }

@router.post("/transactions/batch-adjustment", status_code=status.HTTP_201_CREATED)
def record_batch_adjustment(
    batch: inventory_schemas.BatchAdjustmentCreate,
    db: Session = Depends(get_db)
):
    """
    Record multiple inventory adjustments at once (daily count).

    This endpoint is optimized for end-of-day inventory counts where
    staff updates quantities for many items at once. All adjustments
    are processed atomically - either all succeed or all fail.
    """
    # Validate all items exist first
    item_ids = [adj.item_id for adj in batch.adjustments]
    items = db.query(InventoryItem).filter(InventoryItem.id.in_(item_ids)).all()

    if len(items) != len(set(item_ids)):
        raise HTTPException(
            status_code=404,
            detail="One or more items not found"
        )

    # Create a map for quick lookup
    items_map = {item.id: item for item in items}

    # Process all adjustments
    created_transactions = []
    updated_items = []

    for adjustment in batch.adjustments:
        item = items_map.get(adjustment.item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {adjustment.item_id} not found")

        previous_qty = item.current_quantity
        new_qty = adjustment.new_quantity
        diff = new_qty - previous_qty

        # Skip if quantity hasn't changed
        if diff == 0:
            continue

        # Update item quantity
        item.current_quantity = new_qty
        updated_items.append(item)

        # Create transaction record
        notes = adjustment.notes or f"Daily count: {previous_qty} → {new_qty}"
        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type=TransactionType.ADJUSTMENT,
            quantity=diff,
            notes=notes,
            recorded_by=batch.recorded_by,
            previous_quantity=previous_qty,
            new_quantity=new_qty
        )
        db.add(transaction)
        created_transactions.append({
            "item_id": item.id,
            "item_name": item.name,
            "previous_quantity": float(previous_qty),
            "new_quantity": float(new_qty),
            "difference": float(diff)
        })

    # Commit all changes atomically
    db.commit()

    return {
        "success": True,
        "message": f"Updated {len(created_transactions)} items",
        "total_items_processed": len(batch.adjustments),
        "items_changed": len(created_transactions),
        "items_unchanged": len(batch.adjustments) - len(created_transactions),
        "recorded_by": batch.recorded_by,
        "changes": created_transactions
    }

@router.get("/transactions", response_model=dict)
def get_transactions(
    item_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get transaction history."""
    query = db.query(InventoryTransaction)
    
    if item_id:
        query = query.filter(InventoryTransaction.item_id == item_id)
    
    if transaction_type:
        query = query.filter(InventoryTransaction.transaction_type == transaction_type)
        
    total = query.count()
    transactions = query.order_by(desc(InventoryTransaction.created_at)).offset(offset).limit(limit).all()
    
    result_transactions = []
    for t in transactions:
        t_dict = inventory_schemas.InventoryTransaction.from_orm(t)
        if t.item:
            t_dict.item_name = t.item.name
        result_transactions.append(t_dict)
        
    return {
        "transactions": result_transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }
