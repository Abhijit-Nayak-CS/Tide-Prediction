import sys
import os
import pandas as pd
import numpy as np
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

from src.exception import PXECustomException
from src.logger import logging
from src.utils import save_object

# =============================================================================
# CHANDIPUR COASTAL INTELLIGENCE & BED ELEVATION FEATURE ENGINEERING LOGIC
# =============================================================================

BED_ELEVATIONS = {
    50: 3.90,
    100: 3.80,
    200: 3.60,
    500: 3.00,
    1000: 2.00
}

def calculate_stump_depths(gauge_level: float) -> dict:
    depths = {}
    for distance, elevation in BED_ELEVATIONS.items():
        depths[f"depth_stump_{distance}m"] = max(0.0, round(gauge_level - elevation, 3))
    return depths

def calculate_exposure(gauge_level: float) -> float:
    exposure = (4.00 - gauge_level) * 500.0
    return float(np.clip(exposure, 0.0, 2000.0))

def evaluate_firing_safety(gauge_level: float, tide_stage: str, wind_speed: float) -> int:
    depth_500m = max(0.0, gauge_level - BED_ELEVATIONS[500])
    exposure = calculate_exposure(gauge_level)

    is_safe = (
        (exposure >= 500.0) and
        (depth_500m == 0.0) and
        (tide_stage in ['Ebb', 'Low Slack']) and
        (wind_speed < 12.0)
    )
    return 1 if is_safe else 0


@dataclass
class DataTransformationConfig:
    preprocessor_obj_file_path: str = os.path.join('artifacts', 'preprocessor.pkl')

class DataTransformation:
    def __init__(self):
        self.data_transformation_config = DataTransformationConfig()

    def get_data_transformer_object(self, df):
        """
        Numerical columns ke liye imputer aur scaler banata hai.
        Strings/Categorical columns ko automatically drop ya handle karta hai.
        """
        try:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            drop_cols = ['id', 'main_gauge_level_m', 'safe_for_testing']
            numerical_features = [col for col in numeric_columns if col not in drop_cols]

            logging.info(f"Selected Numerical Features for transformation: {numerical_features}")

            num_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler())
                ]
            )

            preprocessor = ColumnTransformer(
                transformers=[
                    ("num_pipeline", num_pipeline, numerical_features)
                ]
            )

            return preprocessor
        except Exception as e:
            raise PXECustomException(e, sys)

    def initiate_data_transformation(self, train_path, test_path):
        try:
            train_df = pd.read_csv(train_path)
            test_df = pd.read_csv(test_path)
            logging.info("Read train and test data completed")

            for col in train_df.columns:
                if train_df[col].dtype == object and col != 'timestamp':
                    try:
                        train_df[col] = pd.to_numeric(train_df[col], errors='coerce')
                        test_df[col] = pd.to_numeric(test_df[col], errors='coerce')
                    except:
                        pass

            train_df.fillna(0, inplace=True)
            test_df.fillna(0, inplace=True)

            logging.info("Obtaining preprocessing object")
            preprocessing_obj = self.get_data_transformer_object(train_df)

            target_column_name = "main_gauge_level_m"
            
            if target_column_name not in train_df.columns:
                raise Exception(f"Target column '{target_column_name}' not found in training dataset!")

            input_feature_train_df = train_df.drop(columns=[target_column_name], errors='ignore')
            target_feature_train_df = train_df[target_column_name]

            input_feature_test_df = test_df.drop(columns=[target_column_name], errors='ignore')
            target_feature_test_df = test_df[target_column_name]

            logging.info("Applying preprocessing object on training and testing dataframes")

            numeric_cols = input_feature_train_df.select_dtypes(include=[np.number]).columns.tolist()
            
            input_feature_train_arr = preprocessing_obj.fit_transform(input_feature_train_df[numeric_cols])
            input_feature_test_arr = preprocessing_obj.transform(input_feature_test_df[numeric_cols])

            train_arr = np.c_[input_feature_train_arr, np.array(target_feature_train_df)]
            test_arr = np.c_[input_feature_test_arr, np.array(target_feature_test_df)]

            logging.info("Saving preprocessing object.")

            save_object(
                file_path=self.data_transformation_config.preprocessor_obj_file_path,
                obj=preprocessing_obj
            )

            return (
                train_arr,
                test_arr,
                self.data_transformation_config.preprocessor_obj_file_path,
            )
        except Exception as e:
            raise PXECustomException(e, sys)