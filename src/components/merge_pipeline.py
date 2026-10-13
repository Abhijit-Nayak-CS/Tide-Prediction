# import sys
# import sqlite3
# from src.database import DatabaseManager
# from src.exception import PXECustomException
# from src.logger import logging

# class MergePipeline:
#     def __init__(self):
#         self.db_manager = DatabaseManager()

#     def merge_staging_to_main(self):
#         """Staging buffer table ke saare records ko Main table mein transfer karta hai aur staging clear kar deta hai"""
#         try:
#             conn = self.db_manager.get_connection()
#             cursor = conn.cursor()

#             # Check karo ki staging table mein data hai ya nahi
#             cursor.execute("SELECT COUNT(*) FROM staging_telemetry")
#             count = cursor.fetchone()[0]

#             if count == 0:
#                 logging.info("Merge Pipeline: Staging table is empty. No data to merge.")
#                 conn.close()
#                 return {"status": "empty", "message": "Staging buffer is empty! No data to push."}

#             # Staging data ko Main table mein insert karo
#             cursor.execute("""
#                 INSERT INTO tide_telemetry (timestamp, day_of_year, hour_of_day, lunar_phase_rad, moon_distance_km, wind_speed_ms, wind_dir_deg, main_gauge_level_m, safe_for_testing)
#                 SELECT timestamp, day_of_year, hour_of_day, lunar_phase_rad, moon_distance_km, wind_speed_ms, wind_dir_deg, main_gauge_level_m, safe_for_testing 
#                 FROM staging_telemetry
#             """)

#             # Staging table ko clear kar do
#             cursor.execute("DELETE FROM staging_telemetry")

#             conn.commit()
#             conn.close()

#             logging.info(f"Successfully merged {count} records from Staging buffer to Main DB!")
#             return {"status": "success", "merged_count": count}

#         except Exception as e:
#             raise PXECustomException(e, sys)







import sys
import sqlite3
from src.database import DatabaseManager
from src.exception import PXECustomException
from src.logger import logging

class MergePipeline:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def merge_staging_to_main(self):
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM staging_telemetry")
            count = cursor.fetchone()[0]

            if count == 0:
                conn.close()
                return {"status": "empty", "message": "Staging buffer is empty! No data to push."}

            cursor.execute("""
                INSERT INTO tide_telemetry (timestamp, day_of_year, hour_of_day, lunar_phase_rad, moon_distance_km, wind_speed_ms, wind_dir_deg, main_gauge_level_m, safe_for_testing)
                SELECT timestamp, day_of_year, hour_of_day, lunar_phase_rad, moon_distance_km, wind_speed_ms, wind_dir_deg, main_gauge_level_m, safe_for_testing 
                FROM staging_telemetry
            """)

            cursor.execute("DELETE FROM staging_telemetry")
            conn.commit()
            conn.close()

            logging.info(f"Successfully merged {count} records from Staging buffer to Main DB!")
            return {"status": "success", "merged_count": count}

        except Exception as e:
            raise PXECustomException(e, sys)