import os
import sys
import pandas as pd
from src.database import DatabaseManager
from src.exception import PXECustomException
from src.logger import logging

def migrate_csv_to_db():
    """Raw CSV dataset ko read karke SQLite database ke 'tide_telemetry' table mein bulk insert karega"""
    try:
        db_manager = DatabaseManager()
        db_manager.init_database()
        
        csv_path = os.path.join("data", "chandipur_tide_1m_dataset.csv")
        if not os.path.exists(csv_path):
            print("[WARNING] CSV file not found in data/ folder. Initialized empty database tables.")
            return

        print("Reading CSV dataset for migration into SQLite database...")
        df = pd.read_csv(csv_path)
        
        conn = db_manager.get_connection()
        df.to_sql("tide_telemetry", conn, if_exists="replace", index=False)
        conn.close()
        
        print("[SUCCESS] CSV data successfully migrated to SQLite database!")
        logging.info("CSV data successfully migrated to SQLite 'tide_telemetry' table.")
    except Exception as e:
        raise PXECustomException(e, sys)

if __name__ == "__main__":
    migrate_csv_to_db()