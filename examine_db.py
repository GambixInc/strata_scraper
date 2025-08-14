#!/usr/bin/env python3
"""
Database Examination Script for Gambix Strata
Run this on your EC2 instance to examine the SQLite database
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for better readability"""
    if not timestamp_str:
        return "N/A"
    try:
        # Handle different timestamp formats
        if 'T' in timestamp_str:
            # ISO format
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            # SQLite format
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def examine_database(db_path: str):
    """Comprehensive database examination"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("🔍 GAMBIX STRATA DATABASE EXAMINATION")
        print("=" * 80)
        print(f"📁 Database: {db_path}")
        print(f"⏰ Examined at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tables found ({len(tables)}): {', '.join(tables)}")
        print()
        
        # Analyze each table
        total_records = 0
        table_stats = {}
        
        for table in tables:
            print(f"📊 {table.upper()} TABLE")
            print("-" * 40)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_stats[table] = count
            total_records += count
            
            print(f"Total records: {count}")
            
            if count > 0:
                # Get column information
                cursor.execute(f"PRAGMA table_info({table})")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
                
                print(f"Columns ({len(columns)}): {', '.join(columns)}")
                
                # Get sample data (first 5 rows)
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                rows = cursor.fetchall()
                
                print(f"Sample data (showing {len(rows)} rows):")
                for i, row in enumerate(rows, 1):
                    formatted_row = []
                    for j, value in enumerate(row):
                        if columns[j] in ['created_at', 'updated_at', 'last_login', 'last_crawl', 'timestamp', 'dismissed_at']:
                            formatted_row.append(f"{columns[j]}: {format_timestamp(str(value))}")
                        elif columns[j] in ['password_hash']:
                            formatted_row.append(f"{columns[j]}: {'***HIDDEN***' if value else 'None'}")
                        elif isinstance(value, str) and len(value) > 50:
                            formatted_row.append(f"{columns[j]}: {value[:50]}...")
                        else:
                            formatted_row.append(f"{columns[j]}: {value}")
                    
                    print(f"  Row {i}:")
                    for field in formatted_row:
                        print(f"    {field}")
                    print()
            else:
                print("No data found")
            
            print()
        
        # Summary
        print("=" * 80)
        print("📈 DATABASE SUMMARY")
        print("=" * 80)
        print(f"Total tables: {len(tables)}")
        print(f"Total records: {total_records}")
        print()
        
        for table, count in table_stats.items():
            print(f"  {table}: {count} records")
        
        # Check for potential issues
        print()
        print("🔍 POTENTIAL ISSUES CHECK")
        print("-" * 40)
        
        # Check for orphaned records
        if 'users' in table_stats and 'projects' in table_stats:
            cursor.execute("""
                SELECT COUNT(*) FROM projects p 
                LEFT JOIN users u ON p.user_id = u.user_id 
                WHERE u.user_id IS NULL
            """)
            orphaned_projects = cursor.fetchone()[0]
            if orphaned_projects > 0:
                print(f"⚠️  Found {orphaned_projects} projects without valid users")
        
        if 'projects' in table_stats and 'pages' in table_stats:
            cursor.execute("""
                SELECT COUNT(*) FROM pages p 
                LEFT JOIN projects pr ON p.project_id = pr.project_id 
                WHERE pr.project_id IS NULL
            """)
            orphaned_pages = cursor.fetchone()[0]
            if orphaned_pages > 0:
                print(f"⚠️  Found {orphaned_pages} pages without valid projects")
        
        # Check for test data
        cursor.execute("SELECT COUNT(*) FROM users WHERE email LIKE '%test%' OR email LIKE '%example%'")
        test_users = cursor.fetchone()[0]
        if test_users > 0:
            print(f"🧪 Found {test_users} test users")
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE domain LIKE '%test%' OR domain LIKE '%example%'")
        test_projects = cursor.fetchone()[0]
        if test_projects > 0:
            print(f"🧪 Found {test_projects} test projects")
        
        # Check for recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM projects 
            WHERE updated_at > datetime('now', '-7 days')
        """)
        recent_projects = cursor.fetchone()[0]
        print(f"📅 {recent_projects} projects updated in last 7 days")
        
        conn.close()
        
        print()
        print("✅ Database examination completed successfully!")
        
    except Exception as e:
        print(f"❌ Error examining database: {e}")
        return False
    
    return True

def export_sample_data(db_path: str, output_file: str = "db_sample.json"):
    """Export sample data to JSON for further analysis"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "database_path": db_path,
            "tables": {}
        }
        
        for table in tables:
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Get sample data (first 10 rows)
            cursor.execute(f"SELECT * FROM {table} LIMIT 10")
            rows = cursor.fetchall()
            
            table_data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    # Convert datetime objects to strings
                    if isinstance(value, str) and ('created_at' in columns[i] or 'updated_at' in columns[i]):
                        row_dict[columns[i]] = format_timestamp(value)
                    elif columns[i] == 'password_hash':
                        row_dict[columns[i]] = '***HIDDEN***' if value else None
                    else:
                        row_dict[columns[i]] = value
                table_data.append(row_dict)
            
            export_data["tables"][table] = {
                "total_records": len(table_data),
                "sample_data": table_data
            }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"📄 Sample data exported to: {output_file}")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")

if __name__ == "__main__":
    import sys
    
    # Default database path
    db_path = "data/gambix_strata.db"
    
    # Allow command line argument for database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"🔍 Examining database: {db_path}")
    print()
    
    # Check if database exists
    import os
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Available database files:")
        for file in os.listdir("."):
            if file.endswith(".db"):
                print(f"  - {file}")
        sys.exit(1)
    
    # Examine the database
    success = examine_database(db_path)
    
    if success:
        # Export sample data
        export_sample_data(db_path)
        
        print()
        print("💡 Next steps:")
        print("  - Review the data above")
        print("  - Check db_sample.json for detailed data")
        print("  - Use 'sqlite3 data/gambix_strata.db' for interactive queries")
        print("  - Run specific queries like: SELECT * FROM users;")
