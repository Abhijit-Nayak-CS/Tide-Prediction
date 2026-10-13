import sys
from src.exception import PXECustomException
from src.logger import logging
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer

class TrainPipeline:
    def __init__(self):
        pass

    def run_pipeline(self):
        try:
            ingestion = DataIngestion()
            train_data_path, test_data_path = ingestion.initiate_data_ingestion()

            transformation = DataTransformation()
            train_arr, test_arr, preprocessor_path = transformation.initiate_data_transformation(
                train_data_path, test_data_path
            )

            trainer = ModelTrainer()
            r2_score = trainer.initiate_model_trainer(train_arr, test_arr)
            
            logging.info(f"Training Pipeline Completed Successfully! Model R2 Score: {r2_score}")
        except Exception as e:
            raise PXECustomException(e, sys)

if __name__ == "__main__":
    pipeline = TrainPipeline()
    pipeline.run_pipeline()