import sys
import os
from datetime import date

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal, init_db
from app.models.inventory_models import InventoryCategory, InventoryItem, InventoryTransaction
from app.models.cash_models import DailyCashCounter
from app.schemas import inventory_schemas, cash_schemas

def verify_backend():
    print("Initializing database...")
    init_db()
    db = SessionLocal()
    
    try:
        print("\n--- Testing Inventory ---")
        
        # 1. Create Category
        print("Creating Category 'Test Dairy'...")
        cat = db.query(InventoryCategory).filter(InventoryCategory.name == "Test Dairy").first()
        if not cat:
            cat = InventoryCategory(name="Test Dairy")
            db.add(cat)
            db.commit()
            db.refresh(cat)
        print(f"Category ID: {cat.id}")
        
        # 2. Create Item
        print("Creating Item 'Test Milk'...")
        item = db.query(InventoryItem).filter(InventoryItem.name == "Test Milk").first()
        if not item:
            item = InventoryItem(
                name="Test Milk",
                unit="L",
                current_quantity=0,
                min_threshold=10,
                category_id=cat.id
            )
            db.add(item)
            db.commit()
            db.refresh(item)
        print(f"Item ID: {item.id}, Qty: {item.current_quantity}")
        
        # 3. Record Purchase (Transaction)
        print("Recording Purchase of 50L...")
        # Note: In a real API call, we'd use the endpoint logic, but here we test models directly
        # to ensure DB schema is correct.
        item.current_quantity += 50
        trans = InventoryTransaction(
            item_id=item.id,
            transaction_type="PURCHASE",
            quantity=50,
            recorded_by="test_script",
            previous_quantity=0,
            new_quantity=50
        )
        db.add(trans)
        db.commit()
        print(f"New Qty: {item.current_quantity}")
        
        print("\n--- Testing Cash Counter ---")
        
        # 4. Open Cash Counter
        today = date.today()
        print(f"Opening Cash Counter for {today}...")
        counter = db.query(DailyCashCounter).filter(DailyCashCounter.date == today).first()
        if not counter:
            counter = DailyCashCounter(
                date=today,
                opening_balance=1000,
                opened_by="test_script",
                notes="Test opening"
            )
            db.add(counter)
            db.commit()
            db.refresh(counter)
            print(f"Counter Opened. ID: {counter.id}, Status: {counter.status}")
        else:
            print(f"Counter already exists. ID: {counter.id}, Status: {counter.status}")
            
        print("\n✅ Backend Verification Successful!")
        
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_backend()
