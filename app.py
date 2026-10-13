"""
=============================================================================
FLASK WEB APPLICATION: app.py
PROJECT: DRDO PXE Chandipur - Coastal Tide, Weather & Range Safety Portal
=============================================================================
"""

import os
import joblib
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import logging

# Filter out frequent background polling requests from polluting log files
class SuppressHealthCheckLogs(logging.Filter):
    def filter(self, record):
        msg = str(record.getMessage())
        return "/api_health" not in msg and "GET /api_health" not in msg

werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.addFilter(SuppressHealthCheckLogs())

# Modular Structure Imports (including get_connection for duplicate checks)
from src.database import init_db, seed_synthetic_data_if_empty, insert_staging_record, get_connection
from src.components.data_transformation import BED_ELEVATIONS, calculate_stump_depths, calculate_exposure, evaluate_firing_safety
from src.components.merge_pipeline import MergePipeline
from src.api.weather_client import WeatherClient
from src.api.astronomy_client import AstronomyClient
from src.exception import PXECustomException
from src.logger import logging

app = Flask(__name__)

MODEL_LEVEL = None
MODEL_SAFE = None
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

# Initialize database and seed baseline data
logging.info("Starting DRDO PXE Chandipur Portal Initialization...")
init_db()
seed_synthetic_data_if_empty()

# Initialize API and Astronomy clients
weather_client = WeatherClient()
astronomy_client = AstronomyClient()
logging.info("WeatherClient and AstronomyClient successfully instantiated.")

level_path = os.path.join(ARTIFACTS_DIR, "tide_level_model.joblib")
safe_path = os.path.join(ARTIFACTS_DIR, "testing_gate_model.joblib")

if os.path.exists(level_path):
    try:
        MODEL_LEVEL = joblib.load(level_path)
        logging.info("LightGBM Regressor model (tide_level_model.joblib) loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load LightGBM Regressor model: {e}")

if os.path.exists(safe_path):
    try:
        MODEL_SAFE = joblib.load(safe_path)
        logging.info("LightGBM Classifier model (testing_gate_model.joblib) loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load LightGBM Classifier model: {e}")

def predict_tide_physics(hour, day_of_year, lunar_phase_rad, moon_dist, wind_speed, wind_dir):
    omega_M2 = 2 * np.pi / 12.4206012
    omega_S2 = 2 * np.pi / 12.0
    omega_N2 = 2 * np.pi / 12.6583475
    omega_K1 = 2 * np.pi / 23.9344721

    daily_lunar_phase_shift = (day_of_year * 0.85) % 24.0
    t_hours = float((hour - daily_lunar_phase_shift) % 24.0)

    distance_factor = 384400.0 / max(350000.0, moon_dist)
    phase_modulation = 1.0 + 0.15 * np.cos(lunar_phase_rad)

    monsoon_offset = 0.20 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
    mean_sea_level = 2.60 + monsoon_offset
    surge = 0.03 * (wind_speed / 10.0) * np.sin(np.radians(wind_dir))

    level = (
        mean_sea_level
        + (1.65 * distance_factor * phase_modulation) * np.cos(omega_M2 * t_hours)
        + (0.65 * distance_factor) * np.cos(omega_S2 * t_hours + 0.4)
        + (0.35 * distance_factor) * np.cos(omega_N2 * t_hours + 1.2)
        + 0.25 * np.cos(omega_K1 * t_hours - 0.8)
        + surge
    )
    return float(np.clip(level, 0.10, 5.40))

def get_environment_simulation(exposure_m, pred_level):
    if exposure_m >= 1200:
        return {
            "title": "Natural Hard Compacted Mudflat Exposed",
            "desc": f"Low tide receded {exposure_m/1000:.1f} km into Bay of Bengal. Natural hard soil allows deployment of tracking radar antennas and recovery vehicles.",
            "tag": "ENVIRONMENT: DRY FIRM MUDFLAT",
            "dist": f"{exposure_m/1000:.1f} KM WATER RECESSION",
            "img": "/static/images/mudflat_dry.png"
        }
    elif exposure_m >= 500:
        return {
            "title": "Moderate Intertidal Zone Recession",
            "desc": f"Seabed corridor exposed up to {exposure_m:.0f}m. Firing window open with standard safety clearance protocols.",
            "tag": "ENVIRONMENT: STABLE SHALLOW SHORE",
            "dist": f"{exposure_m:.0f} M EXPOSURE",
            "img": "/static/images/mudflat_moderate.png"
        }
    else:
        return {
            "title": "High Tide Coastal Ingress / Sea Water Inundation",
            "desc": f"Water level at {pred_level:.2f}m. Mudflat completely submerged by incoming tide. Firing range restricted.",
            "tag": "ENVIRONMENT: FLOODED / SUBMERGED",
            "dist": "0.0 KM (HIGH TIDE INGRESS)",
            "img": "/static/images/mudflat_flooded.png"
        }

@app.route("/")
def index():
    logging.info("Home page dashboard accessed by operator.")
    return render_template("index.html")

@app.route("/api_health", methods=["GET"])
def api_health():
    return jsonify({
        "weather_api_healthy": weather_client.api_status,
        "astronomy_client_healthy": True
    })

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json or {}
        date_str = data.get("date", "2026-10-08")
        hour = float(data.get("hour", 10))

        logging.info(f"Prediction request received for Date: {date_str}, Hour: {hour}")

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_year = dt.timetuple().tm_yday

        # 1. Fetch dynamic weather
        weather_data = weather_client.fetch_live_weather(date_str, hour)
        wind_speed = weather_data.get("wind_speed_ms", 5.5)
        wind_dir = weather_data.get("wind_dir_deg", 180.0)

        # 2. Fetch astronomical telemetry
        astro_data = astronomy_client.get_astronomy_data(date_str, hour)
        lunar_phase = astro_data.get("lunar_phase_rad", 3.14)
        moon_dist = astro_data.get("moon_distance_km", 381600.0)

        features_df = pd.DataFrame([{
            'day_of_year': day_of_year, 'hour_of_day': hour,
            'lunar_phase_rad': lunar_phase, 'moon_distance_km': moon_dist,
            'wind_speed_ms': wind_speed, 'wind_dir_deg': wind_dir
        }])

        if MODEL_LEVEL is not None:
            try:
                pred_level = float(MODEL_LEVEL.predict(features_df)[0])
                logging.info(f"LightGBM model successfully predicted water level: {pred_level:.3f}m")
            except Exception as ml_err:
                logging.warning(f"LightGBM prediction failed ({ml_err}), falling back to physics math model.")
                pred_level = predict_tide_physics(hour, day_of_year, lunar_phase, moon_dist, wind_speed, wind_dir)
        else:
            logging.info("LightGBM Regressor not loaded, using physics math model.")
            pred_level = predict_tide_physics(hour, day_of_year, lunar_phase, moon_dist, wind_speed, wind_dir)

        pred_level = round(float(np.clip(pred_level, 0.10, 5.40)), 3)

        prev_l = predict_tide_physics(hour - 0.5, day_of_year, lunar_phase, moon_dist, wind_speed, wind_dir)
        next_l = predict_tide_physics(hour + 0.5, day_of_year, lunar_phase, moon_dist, wind_speed, wind_dir)
        rate_of_change = round(next_l - prev_l, 3)

        if rate_of_change > 0.15:
            tide_stage, tide_badge = "Flood (Rapid Inward Ingress)", "badge-flood"
        elif rate_of_change < -0.15:
            tide_stage, tide_badge = "Ebb (Seaward Receding Flow)", "badge-ebb"
        elif pred_level > 3.0:
            tide_stage, tide_badge = "High Slack (Peak Level)", "badge-high"
        else:
            tide_stage, tide_badge = "Low Slack (Lowest Level)", "badge-low"

        exposure_m = round(calculate_exposure(pred_level), 1)
        raw_stump_depths = calculate_stump_depths(pred_level)

        stumps_data = []
        depth_at_500m = raw_stump_depths.get("depth_stump_500m", 0.0)

        for dist, elev in BED_ELEVATIONS.items():
            sub_depth = raw_stump_depths.get(f"depth_stump_{dist}m", 0.0)
            is_dry = (sub_depth == 0.0)
            stumps_data.append({
                "distance": dist, "bed_elevation": elev,
                "water_depth": sub_depth, "is_dry": is_dry,
                "status": "DRY & SOLID" if is_dry else f"FLOODED ({sub_depth:.2f} m)"
            })

        if MODEL_SAFE is not None:
            try:
                is_safe = int(MODEL_SAFE.predict(features_df)[0]) == 1
            except Exception:
                is_safe = evaluate_firing_safety(pred_level, 'Ebb' if 'Ebb' in tide_stage else ('Low Slack' if 'Low Slack' in tide_stage else 'Other'), wind_speed) == 1
        else:
            is_safe = evaluate_firing_safety(pred_level, 'Ebb' if 'Ebb' in tide_stage else ('Low Slack' if 'Low Slack' in tide_stage else 'Other'), wind_speed) == 1

        reasons = [
            {"pass": exposure_m >= 500.0, "text": f"Mudflat corridor exposed: {exposure_m:.1f}m (Limit: >= 500m)."},
            {"pass": depth_at_500m == 0.0, "text": f"500m marker depth: {depth_at_500m:.2f}m (Target: 0.00m dry floor)."},
            {"pass": ("Ebb" in tide_stage or "Low Slack" in tide_stage), "text": f"Kinematic tidal phase: {tide_stage}."},
            {"pass": wind_speed < 12.0, "text": f"Wind velocity: {wind_speed:.1f} m/s (Limit: < 12.0 m/s)."}
        ]

        is_flooded_or_unsafe = (exposure_m < 500.0) or (depth_at_500m > 0.0) or (wind_speed >= 12.0) or ("Flood" in tide_stage)
        is_rapidly_rising = rate_of_change > 0.15

        if is_flooded_or_unsafe:
            range_state = "RESTRICTED"
            banner_title = "RANGE STATE: FIRING RESTRICTED (UNSAFE)"
            banner_desc = "Mudflat submerged, high wind, or flood tide in progress. Firing prohibited."
            badge_class = "badge-danger"
        elif is_rapidly_rising:
            range_state = "WARNING"
            banner_title = "⚠️ WARNING: WATER LEVEL INCREASING RAPIDLY"
            banner_desc = "Water level is increasing rapidly. Decide whether to fire or hold based on mission requirements."
            badge_class = "badge-warning"
        else:
            range_state = "CLEAR"
            banner_title = "RANGE STATE: CLEAR FOR FIRING (SAFE)"
            banner_desc = "Compacted intertidal floor analysis optimal. Firing corridor clear."
            badge_class = "badge-success"

        mahaul = get_environment_simulation(exposure_m, pred_level)

        forecast_24h = []
        for h in range(24):
            f_lev = round(predict_tide_physics(h, day_of_year, lunar_phase, moon_dist, wind_speed, wind_dir), 3)
            f_exp = calculate_exposure(f_lev)
            forecast_24h.append({
                "label": f"{h:02d}:00", "water_level": f_lev,
                "exposure_m": f_exp, "safe": 1 if (f_exp >= 500.0 and (f_lev <= 3.0) and wind_speed < 12.0) else 0
            })

        logging.info(f"Prediction successful. Range State: {range_state}, Gauge Level: {pred_level}m")

        return jsonify({
            "status": "success",
            "prediction": {
                "gauge_level_m": pred_level, "exposure_m": exposure_m,
                "rate_of_change_m_hr": rate_of_change, "tide_stage": tide_stage,
                "tide_badge": tide_badge, "is_safe": 1 if is_safe else 0,
                "range_state": range_state,
                "banner_title": banner_title,
                "banner_desc": banner_desc,
                "badge_class": badge_class,
                "reasons": reasons, "weather": weather_data, "mahaul": mahaul,
                "stumps": stumps_data, "forecast_24h": forecast_24h,
                "api_sources": {
                    "weather_source": weather_data.get("source"),
                    "astronomy_source": astro_data.get("source")
                }
            }
        })
    except Exception as e:
        logging.error(f"Inference Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/save_staging", methods=["POST"])
def save_staging():
    try:
        data = request.json or {}
        gauges = data.get("gauges_detail", {})
        
        main_level = gauges.get("g_1000m", gauges.get("g_500m", 2.5))
        date_str = data.get("date", "2026-10-08")
        hour = float(data.get("hour", 10))

        # [DUPLICATE PREVENTION]: Check if identical record was saved within last 5 seconds
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM staging_telemetry 
            WHERE hour_of_day = ? AND main_gauge_level_m = ? 
            AND datetime(timestamp) >= datetime('now', '-5 seconds')
        """, (float(hour), round(float(main_level), 3)))
        duplicate_count = cursor.fetchone()[0]
        conn.close()

        if duplicate_count > 0:
            logging.warning("Duplicate staging submission blocked by backend guard.")
            return jsonify({
                "status": "success", 
                "commit_hash": "PXE-DUPLICATE-BLOCKED", 
                "message": "Duplicate submission successfully prevented."
            })

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_year = dt.timetuple().tm_yday

        # Live telemetry fetch
        w_data = weather_client.fetch_live_weather(date_str, hour)
        a_data = astronomy_client.get_astronomy_data(date_str, hour)
        
        wind_speed = w_data.get("wind_speed_ms", 5.5)
        wind_dir = w_data.get("wind_dir_deg", 180.0)
        lunar_phase = a_data.get("lunar_phase_rad", 3.14)
        moon_dist = a_data.get("moon_distance_km", 381600.0)

        prev_l = predict_tide_physics(hour - 0.5, day_of_year, lunar_phase, moon_dist, wind_speed, wind_dir)
        next_l = predict_tide_physics(hour + 0.5, day_of_year, lunar_phase, moon_dist, wind_speed, wind_dir)
        rate_of_change = round(next_l - prev_l, 3)

        if rate_of_change > 0.15:
            tide_stage = "Flood (Rapid Inward Ingress)"
        elif rate_of_change < -0.15:
            tide_stage = "Ebb (Seaward Receding Flow)"
        elif float(main_level) > 3.0:
            tide_stage = "High Slack (Peak Level)"
        else:
            tide_stage = "Low Slack (Lowest Level)"

        exposure_m = round(calculate_exposure(float(main_level)), 1)
        stump_depths = calculate_stump_depths(float(main_level))

        raw_str = f"{datetime.now()}-{hour}-{main_level}"
        commit_hash = hashlib.sha256(raw_str.encode()).hexdigest()[:10]
        
        record = {
            'commit_hash': f"PXE-CMT-{commit_hash}",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'day_of_year': int(day_of_year),
            'hour_of_day': float(hour),
            'lunar_phase_rad': round(float(lunar_phase), 4),
            'moon_distance_km': round(float(moon_dist), 2),
            'wind_speed_ms': round(float(wind_speed), 2),
            'wind_dir_deg': round(float(wind_dir), 2),
            'main_gauge_level_m': round(float(main_level), 3),
            'rate_of_change_m_hr': round(float(rate_of_change), 3),
            'tide_stage': str(tide_stage),
            'depth_stump_50m': round(float(stump_depths.get('depth_stump_500m', 0.0) if 'depth_stump_500m' in stump_depths else stump_depths.get('depth_stump_50m', 0.0)), 3),
            'depth_stump_100m': round(float(stump_depths.get('depth_stump_100m', 0.0)), 3),
            'depth_stump_200m': round(float(stump_depths.get('depth_stump_200m', 0.0)), 3),
            'depth_stump_500m': round(float(stump_depths.get('depth_stump_500m', 0.0)), 3),
            'depth_stump_1000m': round(float(stump_depths.get('depth_stump_1000m', 0.0)), 3),
            'intertidal_exposure_m': round(float(exposure_m), 1),
            'safe_for_testing': int(data.get("is_safe", 1))
        }
        
        insert_staging_record(record)
        logging.info(f"Operator Staging Record Committed Successfully with full telemetry: [PXE-CMT-{commit_hash}]")
        return jsonify({"status": "success", "commit_hash": f"PXE-CMT-{commit_hash}", "message": "Committed to database staging table with complete derived calculations."})
    except Exception as e:
        logging.error(f"Database Staging Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/merge_staging", methods=["POST"])
def merge_staging_data():
    try:
        logging.info("Initiating merge from staging table to main historical database...")
        pipeline = MergePipeline()
        result = pipeline.merge_staging_to_main()
        logging.info(f"Complete merge operation: {result}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Merge Staging Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)