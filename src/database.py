
import os
import sys
import sqlite3
import pandas as pd
from src.exception import PXECustomException
from src.logger import logging

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "pxe_tide_portal.db")
# CSV file can be in root or data folder
CSV_PATH_ROOT = "chandipur_tide_1m_dataset.csv"
CSV_PATH_DATA = os.path.join(DB_DIR, "chandipur_tide_1m_dataset.csv")

class DatabaseManager:
    def __init__(self):
        self.db_dir = DB_DIR
        self.db_path = DB_PATH
        os.makedirs(self.db_dir, exist_ok=True)

    def get_connection(self):
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            raise PXECustomException(e, sys)

    def init_database(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 17-Feature Schema matching CSV exactly
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tide_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    day_of_year INTEGER,
                    hour_of_day REAL,
                    lunar_phase_rad REAL,
                    moon_distance_km REAL,
                    wind_speed_ms REAL,
                    wind_dir_deg REAL,
                    main_gauge_level_m REAL,
                    rate_of_change_m_hr REAL,
                    tide_stage TEXT,
                    depth_stump_50m REAL,
                    depth_stump_100m REAL,
                    depth_stump_200m REAL,
                    depth_stump_500m REAL,
                    depth_stump_1000m REAL,
                    intertidal_exposure_m REAL,
                    safe_for_testing INTEGER
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staging_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commit_hash TEXT,
                    timestamp TEXT,
                    day_of_year INTEGER,
                    hour_of_day REAL,
                    lunar_phase_rad REAL,
                    moon_distance_km REAL,
                    wind_speed_ms REAL,
                    wind_dir_deg REAL,
                    main_gauge_level_m REAL,
                    rate_of_change_m_hr REAL,
                    tide_stage TEXT,
                    depth_stump_50m REAL,
                    depth_stump_100m REAL,
                    depth_stump_200m REAL,
                    depth_stump_500m REAL,
                    depth_stump_1000m REAL,
                    intertidal_exposure_m REAL,
                    safe_for_testing INTEGER
                )
            """)

            conn.commit()
            conn.close()
            logging.info("Database successfully initialized with 17-feature Main and Staging tables.")
        except Exception as e:
            raise PXECustomException(e, sys)

def get_connection():
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        raise PXECustomException(e, sys)

def init_db():
    manager = DatabaseManager()
    manager.init_database()

def seed_synthetic_data_if_empty():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tide_telemetry")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            csv_file = CSV_PATH_ROOT if os.path.exists(CSV_PATH_ROOT) else CSV_PATH_DATA
            if os.path.exists(csv_file):
                logging.info(f"Loading dataset from {csv_file} into tide_telemetry in chunks...")
                chunk_size = 100000
                for chunk in pd.read_csv(csv_file, chunksize=chunk_size):
                    conn = get_connection()
                    chunk.to_sql('tide_telemetry', conn, if_exists='append', index=False)
                    conn.close()
                logging.info("Full CSV dataset successfully loaded into main database!")
            else:
                logging.warning(f"CSV dataset file not found! Please ensure chandipur_tide_1m_dataset.csv is present.")
    except Exception as e:
        logging.error(f"CSV Loading Error: {e}")

def insert_staging_record(record: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO staging_telemetry (
                commit_hash, timestamp, day_of_year, hour_of_day,
                lunar_phase_rad, moon_distance_km, wind_speed_ms,
                wind_dir_deg, main_gauge_level_m, rate_of_change_m_hr,
                tide_stage, depth_stump_50m, depth_stump_100m,
                depth_stump_200m, depth_stump_500m, depth_stump_1000m,
                intertidal_exposure_m, safe_for_testing
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.get('commit_hash'),
            record.get('timestamp'),
            record.get('day_of_year'),
            record.get('hour_of_day'),
            record.get('lunar_phase_rad'),
            record.get('moon_distance_km'),
            record.get('wind_speed_ms'),
            record.get('wind_dir_deg'),
            record.get('main_gauge_level_m'),
            record.get('rate_of_change_m_hr', 0.0),
            record.get('tide_stage', 'Unknown'),
            record.get('depth_stump_50m', 0.0),
            record.get('depth_stump_100m', 0.0),
            record.get('depth_stump_200m', 0.0),
            record.get('depth_stump_500m', 0.0),
            record.get('depth_stump_1000m', 0.0),
            record.get('intertidal_exposure_m', 0.0),
            record.get('safe_for_testing', 1)
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        raise PXECustomException(e, sys)