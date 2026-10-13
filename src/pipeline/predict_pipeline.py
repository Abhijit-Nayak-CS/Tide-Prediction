# import sys
# import os
# import joblib
# import pandas as pd
# from src.exception import PXECustomException
# from src.logger import logging

# class PredictPipeline:
#     def __init__(self):
#         self.artifacts_dir = "artifacts"
#         self.level_model_path = os.path.join(self.artifacts_dir, "tide_level_model.joblib")
#         self.safe_model_path = os.path.join(self.artifacts_dir, "testing_gate_model.joblib")

#     def predict(self, features_df):
#         try:
#             if not os.path.exists(self.level_model_path) or not os.path.exists(self.safe_model_path):
#                 raise FileNotFoundError("Model artifacts (.joblib) nahi mile! Pehle train_pipeline.py run karein.")
            
#             level_model = joblib.load(self.level_model_path)
#             safe_model = joblib.load(self.safe_model_path)
            
#             pred_level = float(level_model.predict(features_df)[0])
#             is_safe = int(safe_model.predict(features_df)[0])
            
#             return pred_level, is_safe
#         except Exception as e:
#             raise PXECustomException(e, sys)

# class CustomData:
#     def __init__(self, day_of_year: int, hour_of_day: float, lunar_phase_rad: float, moon_distance_km: float, wind_speed_ms: float, wind_dir_deg: float):
#         self.day_of_year = day_of_year
#         self.hour_of_day = hour_of_day
#         self.lunar_phase_rad = lunar_phase_rad
#         self.moon_distance_km = moon_distance_km
#         self.wind_speed_ms = wind_speed_ms
#         self.wind_dir_deg = wind_dir_deg

#     def get_data_as_data_frame(self):
#         try:
#             custom_data_input_dict = {
#                 "day_of_year": [self.day_of_year],
#                 "hour_of_day": [self.hour_of_day],
#                 "lunar_phase_rad": [self.lunar_phase_rad],
#                 "moon_distance_km": [self.moon_distance_km],
#                 "wind_speed_ms": [self.wind_speed_ms],
#                 "wind_dir_deg": [self.wind_dir_deg],
#             }
#             return pd.DataFrame(custom_data_input_dict)
#         except Exception as e:
#             raise PXECustomException(e, sys)





import sys
import os
import joblib
import numpy as np
import pandas as pd
from src.exception import PXECustomException
from src.logger import logging

class PredictPipeline:
    def __init__(self):
        self.artifacts_dir = "artifacts"
        self.level_model_path = os.path.join(self.artifacts_dir, "tide_level_model.joblib")
        self.safe_model_path = os.path.join(self.artifacts_dir, "testing_gate_model.joblib")
        self.preprocessor_path = os.path.join(self.artifacts_dir, "preprocessor.pkl")

    def predict(self, features_df):
        try:
            if not os.path.exists(self.level_model_path) or not os.path.exists(self.safe_model_path):
                raise FileNotFoundError("Model artifacts (.joblib) nahi mile! Pehle train_pipeline.py run karein.")
            
            level_model = joblib.load(self.level_model_path)
            safe_model = joblib.load(self.safe_model_path)
            
            # Agar preprocessor maujood hai toh scaling apply karein taaki global standards match ho sakein
            if os.path.exists(self.preprocessor_path):
                preprocessor = joblib.load(self.preprocessor_path)
                numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
                scaled_array = preprocessor.transform(features_df[numeric_cols])
                # DataFrame preserve karke prediction chalayein
                transformed_df = pd.DataFrame(scaled_array, columns=numeric_cols)
            else:
                transformed_df = features_df

            pred_level = float(level_model.predict(transformed_df)[0])
            is_safe = int(safe_model.predict(transformed_df)[0])
            
            return pred_level, is_safe
        except Exception as e:
            raise PXECustomException(e, sys)

class CustomData:
    def __init__(self, day_of_year: int, hour_of_day: float, lunar_phase_rad: float = None, moon_distance_km: float = None, wind_speed_ms: float = 5.5, wind_dir_deg: float = 180.0):
        self.day_of_year = day_of_year
        self.hour_of_day = hour_of_day
        
        # World-Standard Harmonic & Astronomical Derivation for Chandipur Coast
        # M2 constituent cycle delay: Rozana ~50-55 minute (0.85 hours) ka phase shift shift hota hai.
        # Isse date badalne par tide graph aur water level bilkul alag aur real-time behavior dikhayega.
        lunar_delay_factor = (self.day_of_year * 0.85) % 24.0
        adjusted_hour = (self.hour_of_day - lunar_delay_factor) % 24.0
        
        # Global Harmonic Moon Phase calculation based on day of year (29.53 days synodic month cycle)
        if lunar_phase_rad is None:
            self.lunar_phase_rad = float((2.0 * np.pi * (self.day_of_year % 29.53)) / 29.53)
        else:
            self.lunar_phase_rad = lunar_phase_rad
            
        if moon_distance_km is None:
            # Perigee / Apogee average orbital fluctuation (~363,000 km to 405,000 km)
            self.moon_distance_km = float(384400.0 + 20000.0 * np.cos(2.0 * np.pi * self.day_of_year / 27.3))
        else:
            self.moon_distance_km = moon_distance_km
            
        self.wind_speed_ms = wind_speed_ms
        self.wind_dir_deg = wind_dir_deg
        
        # Store adjusted hour for model features if trained on phase-shifted time
        self.effective_hour = adjusted_hour

    def get_data_as_data_frame(self):
        try:
            custom_data_input_dict = {
                "day_of_year": [self.day_of_year],
                "hour_of_day": [self.effective_hour], # Using harmonically shifted hour for accurate date reactivity
                "lunar_phase_rad": [self.lunar_phase_rad],
                "moon_distance_km": [self.moon_distance_km],
                "wind_speed_ms": [self.wind_speed_ms],
                "wind_dir_deg": [self.wind_dir_deg],
            }
            return pd.DataFrame(custom_data_input_dict)
        except Exception as e:
            raise PXECustomException(e, sys)