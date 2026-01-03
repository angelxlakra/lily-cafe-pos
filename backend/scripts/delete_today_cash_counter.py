import sqlite3
import os
from datetime import date
import sys

# Add parent directory to path to allow imports if needed, 
# although we are using raw sqlite3 here for simplicity and robustness against env issues.

# Get database path relative to this script
# Assumes script is in backend/scripts/ and db is in backend/
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../restaurant.db")

def delete_today_counter():
    print(f"Connecting to database at: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = date.today()
        print(f"Searching for cash counter record for today: {today}")
        
        # Check if exists
        # Note: date is stored as YYYY-MM-DD string or date type in SQLite
        cursor.execute("SELECT id, date, opening_balance FROM daily_cash_counter WHERE date = ?", (today,))
        row = cursor.fetchone()
        
        if not row:
            print("No cash counter record found for today.")
            
            # Optional: Show recent ones
            print("\nRecent entries:")
            cursor.execute("SELECT id, date, opening_balance FROM daily_cash_counter ORDER BY date DESC LIMIT 3")
            for r in cursor.fetchall():
                print(f"  ID={r[0]}, Date={r[1]}, Opening Balance={r[2]}")
                
            conn.close()
            return

        print(f"\nFOUND RECORD: ID={row[0]}, Date={row[1]}, Opening Balance={row[2]}")
        
        confirm = input("Are you sure you want to DELETE this record? (yes/no): ")
        if confirm.lower() == 'yes':
            cursor.execute("DELETE FROM daily_cash_counter WHERE id = ?", (row[0],))
            conn.commit()
            print("✅ Successfully deleted today's cash counter.")
        else:
            print("❌ Operation cancelled.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    delete_today_counter()
