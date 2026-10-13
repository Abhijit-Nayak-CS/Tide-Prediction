# import os
# import sys
# import pandas as pd
# import sqlite3
# from src.exception import PXECustomException
# from src.logger import logging

# class DataIngestionConfig:
#     def __init__(self):
#         self.train_data_path = os.path.join('artifacts', 'train.csv')
#         self.test_data_path = os.path.join('artifacts', 'test.csv')
#         self.raw_data_path = os.path.join('artifacts', 'raw.csv')
#         self.db_path = os.path.join('data', 'pxe_tide_portal.db')

# class DataIngestion:
#     def __init__(self):
#         self.ingestion_config = DataIngestionConfig()

#     def initiate_data_ingestion(self):
#         """Database se data read karke train aur test CSV mein split karega"""
#         logging.info("Entered data ingestion component method")
#         try:
#             os.makedirs(os.path.dirname(self.ingestion_config.raw_data_path), exist_ok=True)
            
#             conn = sqlite3.connect(self.db_path)
#             df = pd.read_sql("SELECT * FROM tide_telemetry", conn)
#             conn.close()
            
#             logging.info("Read dataset successfully from SQLite database")
#             df.to_csv(self.ingestion_config.raw_data_path, index=False)

#             from sklearn.model_selection import train_test_split
#             train_set, test_set = train_test_split(df, test_size=0.2, random_state=42)

#             train_set.to_csv(self.ingestion_config.train_data_path, index=False, header=True)
#             test_set.to_csv(self.ingestion_config.test_data_path, index=False, header=True)

#             logging.info("Data Ingestion completed successfully")
#             return (
#                 self.ingestion_config.train_data_path,
#                 self.ingestion_config.test_data_path
#             )
#         except Exception as e:
#             raise PXECustomException(e, sys)






import os
import sys
import pandas as pd
import sqlite3
from src.exception import PXECustomException
from src.logger import logging
from src.database import DatabaseManager
from sklearn.model_selection import train_test_split
from dataclasses import dataclass

@dataclass
class DataIngestionConfig:
    train_data_path: str = os.path.join('artifacts', 'train.csv')
    test_data_path: str = os.path.join('artifacts', 'test.csv')
    raw_data_path: str = os.path.join('artifacts', 'raw.csv')

class DataIngestion:
    def __init__(self):
        self.ingestion_config = DataIngestionConfig()
        self.db_manager = DatabaseManager()

    def initiate_data_ingestion(self):
        logging.info("Entered the data ingestion method/component")
        try:
            # SQLite Database se direct 'tide_telemetry' table read karna
            conn = self.db_manager.get_connection()
            logging.info("Reading dataset from SQLite database table: tide_telemetry")
            df = pd.read_sql("SELECT * FROM tide_telemetry", conn)
            conn.close()

            os.makedirs(os.path.dirname(self.ingestion_config.train_data_path), exist_ok=True)

            # Save raw artifacts
            df.to_csv(self.ingestion_config.raw_data_path, index=False, header=True)
            
            logging.info("Train-test split initiated")
            train_set, test_set = train_test_split(df, test_size=0.2, random_state=42)

            train_set.to_csv(self.ingestion_config.train_data_path, index=False, header=True)
            test_set.to_csv(self.ingestion_config.test_data_path, index=False, header=True)

            logging.info("Ingestion of data is completed successfully")

            return (
                self.ingestion_config.train_data_path,
                self.ingestion_config.test_data_path
            )
        except Exception as e:
            raise PXECustomException(e, sys)