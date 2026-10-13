import ephem
import numpy as np
from datetime import datetime
from src.logger import logging
from src.exception import PXECustomException
import sys

class AstronomyClient:
    def __init__(self):
        pass

    def get_astronomy_data(self, target_date_str: str, hour: float):
        """
        Calculates lunar phase (in radians) and moon distance (in km) 
        for a given date and hour using the offline 'ephem' library.
        """
        try:
            dt = datetime.strptime(target_date_str, "%Y-%m-%d")
            
            # Extract integer hour and minute
            h = int(hour)
            m = int((hour % 1) * 60)
            
            # Set ephem date
            ephem_date = ephem.Date(datetime(dt.year, dt.month, dt.day, h, m))
            
            moon = ephem.Moon(ephem_date)
            sun = ephem.Sun(ephem_date)
            
            # Moon distance in AU converted to kilometers (1 AU = 149,597,870.7 km)
            moon_distance_km = float(moon.earth_distance * 149597870.7)
            
            # Calculate angular separation (elongation) between Sun and Moon in radians
            # 0 = New Moon, ~3.14 (pi) = Full Moon
            elongation = ephem.separation((sun.ra, sun.dec), (moon.ra, moon.dec))
            lunar_phase_rad = float(elongation)

            logging.info(f"Astronomy telemetry calculated: Distance={moon_distance_km:.1f} km, Phase={lunar_phase_rad:.2f} rad")

            return {
                "lunar_phase_rad": lunar_phase_rad,
                "moon_distance_km": moon_distance_km,
                "source": "ephem_offline_library",
                "api_healthy": True
            }

        except Exception as e:
            logging.error(f"Astronomy Calculation Error: {str(e)}")
            # Fallback default values if calculation fails
            return {
                "lunar_phase_rad": 3.14,
                "moon_distance_km": 381600.0,
                "source": "fallback_default",
                "api_healthy": False
            }