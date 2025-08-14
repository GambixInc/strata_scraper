#!/usr/bin/env python3
"""
Add cognito_user_id column to existing users table
"""

import sqlite3
import os

def add_cognito_column():
    """Add cognito_user_id column to users table if it doesn't exist"""
    db_path = "data/gambix_strata.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if cognito_user_id column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'cognito_user_id' not in columns:
                print("Adding cognito_user_id column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN cognito_user_id TEXT UNIQUE")
                print("✅ cognito_user_id column added successfully")
            else:
                print("✅ cognito_user_id column already exists")
                
    except Exception as e:
        print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_cognito_column()
