import os
import sys
import requests
import numpy as np
from datetime import datetime
from src.database import get_connection
from src.logger import logging
from src.exception import PXECustomException

class WeatherClient:
    def __init__(self, api_key: str = None):
        # OpenWeatherMap API Key integrated directly
        self.api_key = api_key or os.getenv("WEATHER_API_KEY", "26cc6b2c48469a9469fd86ce6560b641")
        # Chandipur, Odisha coordinates (Lat, Lon)
        self.lat = 21.4428
        self.lon = 87.0394
        self.api_status = False  # Tracks whether the live API is currently healthy

    def fetch_live_weather(self, target_date_str: str, hour: float):
        """
        Tries to fetch live/forecast weather from OpenWeatherMap API.
        Returns dict with wind_speed_ms, wind_dir_deg, temp, pressure, humidity, visibility_km and sets api_status = True.
        If any failure occurs, triggers fallback mechanisms and sets api_status = False.
        """
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                wind_data = data.get("wind", {})
                main_data = data.get("main", {})
                
                wind_speed = float(wind_data.get("speed", 5.5))  # m/s
                wind_dir = float(wind_data.get("deg", 180.0))    # degrees
                temp_c = float(main_data.get("temp", 28.0))
                pressure = float(main_data.get("pressure", 1013.25))
                humidity = float(main_data.get("humidity", 75.0))
                
                # OpenWeather returns visibility in meters; convert to kilometers
                visibility_m = data.get("visibility", 10000)
                visibility_km = round(float(visibility_m) / 1000.0, 1)
                
                self.api_status = True
                logging.info("Weather API successfully fetched live atmospheric data.")
                
                return {
                    "wind_speed_ms": wind_speed,
                    "wind_dir_deg": wind_dir,
                    "temperature_c": temp_c,
                    "pressure_hpa": pressure,
                    "humidity_pct": humidity,
                    "visibility_km": visibility_km,
                    "source": "live_api",
                    "api_healthy": True
                }
            else:
                logging.warning(f"Weather API returned status code {response.status_code}. Switching to fallback.")
                self.api_status = False
                return self._trigger_fallback(target_date_str, hour)

        except Exception as e:
            logging.error(f"Weather API Connection Error: {str(e)}. Switching to fallback.")
            self.api_status = False
            return self._trigger_fallback(target_date_str, hour)

    def _trigger_fallback(self, target_date_str: str, hour: float):
        """
        Double-tier Fallback Strategy:
        1. Attempts to fetch historical average from SQLite database (`tide_telemetry`).
        2. If database is empty or fails, falls back to local mathematical physics formulas.
        """
        try:
            dt = datetime.strptime(target_date_str, "%Y-%m-%d")
            day_of_year = dt.timetuple().tm_yday
            
            # Tier 1: Database Historical Lookup
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(wind_speed_ms), AVG(wind_dir_deg) 
                FROM tide_telemetry 
                WHERE day_of_year BETWEEN ? AND ?
            """, (max(1, day_of_year - 5), min(365, day_of_year + 5)))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] is not None:
                db_wind_speed = float(row[0])
                db_wind_dir = float(row[1] if row[1] is not None else 180.0)
                
                logging.info("Fallback: Successfully retrieved weather proxy from database historical averages.")
                
                math_weather = self._compute_math_fallback(day_of_year, hour, db_wind_speed)
                math_weather["source"] = "database_fallback"
                math_weather["api_healthy"] = False
                return math_weather

        except Exception as db_err:
            logging.warning(f"Database Fallback Error: {str(db_err)}. Using pure math fallback.")

        # Tier 2: Pure Mathematical Fallback Formula
        dt = datetime.strptime(target_date_str, "%Y-%m-%d")
        day_of_year = dt.timetuple().tm_yday
        math_weather = self._compute_math_fallback(day_of_year, hour, wind_speed=5.5)
        math_weather["source"] = "math_formula_fallback"
        math_weather["api_healthy"] = False
        
        logging.info("Fallback: Using local mathematical physics weather model.")
        return math_weather

    def _compute_math_fallback(self, day_of_year: int, hour: float, wind_speed: float):
        """
        Local mathematical simulation for weather conditions based on season and hour.
        """
        is_monsoon = 150 <= day_of_year <= 270
        is_summer = 60 <= day_of_year < 150
        is_winter = day_of_year > 320 or day_of_year < 45

        base_temp = 34.0 if is_summer else (30.5 if is_monsoon else (22.0 if is_winter else 28.0))
        humidity_base = 88.0 if is_monsoon else (74.0 if is_summer else (62.0 if is_winter else 70.0))

        temp_c = round(float(base_temp + 4.5 * np.sin(np.pi * (hour - 8) / 12.0)), 1)
        humidity = round(float(np.clip(humidity_base - 1.2 * (temp_c - base_temp) + (wind_speed * 0.4), 40.0, 98.0)), 1)
        pressure_hpa = round(float(1013.25 - 0.12 * (wind_speed ** 1.5) - (2.5 if is_monsoon else 0.0)), 1)

        return {
            "wind_speed_ms": wind_speed,
            "wind_dir_deg": 180.0,
            "temperature_c": temp_c,
            "pressure_hpa": pressure_hpa,
            "humidity_pct": humidity,
            "visibility_km": 11.5  # Standard clear fallback optical visibility
        }