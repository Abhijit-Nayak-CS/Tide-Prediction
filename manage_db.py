import argparse
import os
from src.database import get_connection, init_db

def clear_staging():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM staging_telemetry")
        conn.commit()
        conn.close()
        print("[SUCCESS] Staging telemetry table has been cleared.")
    except Exception as e:
        print(f"[ERROR] Failed to clear staging table: {e}")

def show_db_status():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tide_telemetry")
        main_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM staging_telemetry")
        staging_count = cursor.fetchone()[0]
        
        conn.close()
        print("--- DRDO PXE PORTAL DATABASE STATUS ---")
        print(f"Main Database Records (tide_telemetry): {main_count}")
        print(f"Staging Records (staging_telemetry): {staging_count}")
    except Exception as e:
        print(f"[ERROR] Could not fetch DB status: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PXE Portal Database & ETL Management Utility")
    parser.add_argument("--clear-staging", action="store_true", help="Clear all records from staging_telemetry table")
    parser.add_argument("--status", action="store_true", help="Show record counts for main and staging tables")
    parser.add_argument("--init", action="store_true", help="Initialize or re-verify database tables")

    args = parser.parse_args()

    if args.clear_staging:
        clear_staging()
    elif args.status:
        show_db_status()
    elif args.init:
        init_db()
        print("[SUCCESS] Database schema initialized/verified.")
    else:
        parser.print_help()





# ==============================================================================
# DRDO PXE CHANDIPUR PORTAL - DATABASE MAINTENANCE CLI CHEATSHEET
# ==============================================================================
# Copy and run these commands directly in your VS Code terminal (from project root)
# ==============================================================================

# 1. Check live record counts in Main DB and Staging table
# python manage_db.py --status

# 2. Clear all temporary records from the Staging table safely
# python manage_db.py --clear-staging

# 3. Initialize or re-verify database tables and 17-feature schema structure
# python manage_db.py --init

# 4. View help guide and available utility commands list
# python manage_db.py --help

# [Future / Planned Commands]
# 5. Create a secure backup copy of the SQLite database
# python manage_db.py --backup

# 6. Force reload baseline CSV dataset into the main database
# python manage_db.py --seed