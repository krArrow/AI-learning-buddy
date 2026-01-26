"""
Database migration script to add missing columns to learning_goals table.
Adds: target_completion_days and target_display_text columns
"""
import sqlite3
from pathlib import Path

def migrate_database():
    """Add missing columns to the learning_goals table."""
    db_path = Path("data/learning_buddy.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(learning_goals)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        # Add target_completion_days if it doesn't exist
        if "target_completion_days" not in columns:
            print("Adding column: target_completion_days")
            cursor.execute("""
                ALTER TABLE learning_goals 
                ADD COLUMN target_completion_days INTEGER
            """)
            print("✓ Added target_completion_days column")
        else:
            print("✓ target_completion_days column already exists")
        
        # Add target_display_text if it doesn't exist
        if "target_display_text" not in columns:
            print("Adding column: target_display_text")
            cursor.execute("""
                ALTER TABLE learning_goals 
                ADD COLUMN target_display_text VARCHAR(100)
            """)
            print("✓ Added target_display_text column")
        else:
            print("✓ target_display_text column already exists")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(learning_goals)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"\nUpdated columns: {columns_after}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    migrate_database()
