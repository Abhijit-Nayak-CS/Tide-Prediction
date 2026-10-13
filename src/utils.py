import os
import sys
import pickle
from src.exception import PXECustomException
from src.logger import logging

def save_object(file_path: str, obj):
    """Model ya preprocessor ko pickle format mein save karne ke liye"""
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, "wb") as file_obj:
            pickle.dump(obj, file_obj)
        logging.info(f"Object successfully saved at: {file_path}")
    except Exception as e:
        raise PXECustomException(e, sys)

def load_object(file_path: str):
    """Saved pickle object ko load karne ke liye"""
    try:
        with open(file_path, "rb") as file_obj:
            return pickle.load(file_obj)
    except Exception as e:
        raise PXECustomException(e, sys)