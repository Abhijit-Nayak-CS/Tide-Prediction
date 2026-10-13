# import os
# import sys
# from lightgbm import LGBMRegressor
# from sklearn.metrics import r2_score, mean_squared_error
# from src.exception import PXECustomException
# from src.logger import logging
# from src.utils import save_object

# class ModelTrainerConfig:
#     def __init__(self):
#         self.trained_model_file_path = os.path.join("artifacts", "model.pkl")

# class ModelTrainer:
#     def __init__(self):
#         self.model_trainer_config = ModelTrainerConfig()

#     def initiate_model_trainer(self, train_array, test_array):
#         """LightGBM Model train karega aur R2/RMSE evaluate karega"""
#         try:
#             logging.info("Splitting training and test input data")
#             X_train, y_train, X_test, y_test = (
#                 train_array[:, :-1],
#                 train_array[:, -1],
#                 test_array[:, :-1],
#                 test_array[:, -1]
#             )

#             model = LGBMRegressor(n_estimators=100, learning_rate=0.05, random_state=42)
#             model.fit(X_train, y_train)

#             predicted = model.predict(X_test)
#             r2 = r2_score(y_test, predicted)
#             rmse = mean_squared_error(y_test, predicted, squared=False)

#             logging.info(f"Model Evaluation Metrics -> R2 Score: {r2:.4f}, RMSE: {rmse:.4f}")

#             save_object(
#                 file_path=self.model_trainer_config.trained_model_file_path,
#                 obj=model
#             )

#             return r2
#         except Exception as e:
#             raise PXECustomException(e, sys)



import os
import sys
import pandas as pd
from lightgbm import LGBMRegressor, LGBMClassifier
from sklearn.metrics import r2_score, mean_squared_error, accuracy_score, classification_report
from src.exception import PXECustomException
from src.logger import logging
from src.utils import save_object

class ModelTrainerConfig:
    def __init__(self):
        self.tide_model_file_path = os.path.join("artifacts", "tide_level_model.joblib")
        self.safety_model_file_path = os.path.join("artifacts", "testing_gate_model.joblib")

class ModelTrainer:
    def __init__(self):
        self.model_trainer_config = ModelTrainerConfig()

    def initiate_model_trainer(self, train_array, test_array):
        """
        LightGBM Regressor (Tide Level) aur Classifier (Safety Gate) dono ko train karega,
        metrics evaluate karega aur joblib format mein artifacts/ folder mein save karega.
        """
        try:
            logging.info("Splitting training and test arrays for dual-model training")
            
            # Assuming last column is Tide Level (Regression) and 2nd last or computed is Safety (Classification)
            X_train, y_train_reg = train_array[:, :-1], train_array[:, -1]
            X_test, y_test_reg = test_array[:, :-1], test_array[:, -1]

            # 1. Train Regressor Model (LightGBM for Tide Gauge Level)
            logging.info("Training LightGBM Regressor for Tide Level Prediction...")
            tide_model = LGBMRegressor(n_estimators=100, learning_rate=0.05, random_state=42)
            tide_model.fit(X_train, y_train_reg)

            preds_reg = tide_model.predict(X_test)
            r2 = r2_score(y_test_reg, preds_reg)
            rmse = mean_squared_error(y_test_reg, preds_reg, squared=False)
            logging.info(f"Tide Regressor Metrics -> R2 Score: {r2:.4f}, RMSE: {rmse:.4f}")

            # 2. Derive Safety Classification Target (1 if Safe, 0 if Restricted)
            y_train_clf = (y_train_reg < 3.0).astype(int)
            y_test_clf = (y_test_reg < 3.0).astype(int)

            logging.info("Training LightGBM Classifier for Firing Range Safety Gate...")
            safety_model = LGBMClassifier(n_estimators=100, learning_rate=0.05, random_state=42)
            safety_model.fit(X_train, y_train_clf)

            preds_clf = safety_model.predict(X_test)
            accuracy = accuracy_score(y_test_clf, preds_clf)
            logging.info(f"Safety Classifier Metrics -> Accuracy: {accuracy:.4f}")

            # Save both models as .joblib in artifacts/
            save_object(file_path=self.model_trainer_config.tide_model_file_path, obj=tide_model)
            save_object(file_path=self.model_trainer_config.safety_model_file_path, obj=safety_model)

            logging.info("Both models successfully trained, evaluated, and saved.")
            return {"r2_score": r2, "rmse": rmse, "accuracy": accuracy}

        except Exception as e:
            raise PXECustomException(e, sys)