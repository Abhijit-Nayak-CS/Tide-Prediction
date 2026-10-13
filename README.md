# 🛡️ DRDO PXE Chandipur - Coastal Defense & Mission Portal

> **Autonomous Intertidal Mudflat Prediction, Weapon Testing & Range Clearance Portal** developed for Proof & Experimental Establishment (PXE), Chandipur, Odisha.

---

## 📋 About The Project
The **DRDO PXE Coastal Defense & Mission Portal** is an advanced, PowerBI-inspired command-and-control web application designed to monitor intertidal mudflat conditions, predict dynamic sea tide levels, and evaluate real-time range safety for weapon testing and tracking operations off the coast of Chandipur.

Chandipur's unique geographical phenomenon—where the sea recedes up to 5 kilometers during low tide—creates vast compacted mudflat corridors. This portal bridges meteorological live APIs, high-precision astronomical calculations, and LightGBM machine learning models to provide automated mission clearance and risk assessment for Range Safety Officers (RSOs).

---

## ✨ Key Features & Architecture Highlights

* **🧠 Machine Learning Pipeline:** Trained models (`tide_level_model.joblib` and `testing_gate_model.joblib`) integrated with a robust pre-processor (`preprocessor.pkl`) to predict precise water levels and range safety states.
* **🌐 Real-Time Atmospheric Telemetry (`src/api/`):** Fetches live wind speed, direction, temperature, pressure, humidity, and optical visibility via OpenWeatherMap API, supported by a double-tier database and mathematical physics fallback.
* **🔭 Astronomical Ephemeris (`astronomy_client.py`):** Computes high-precision lunar phases, moon distances, and gravitational tidal modulations using the `ephem` library.
* **🔄 Modular Pipeline Architecture (`src/components/` & `src/pipeline/`):** Clean separation of concerns featuring dedicated modules for Data Ingestion, Data Transformation, Model Training, Prediction, and Staging-to-Production DB Merging.
* **🗄️ Dual-Database & Staging Pattern (`pxe_portal.db`):** Implements an operator staging workflow (`staging_telemetry`) with secure cryptographic commit hashes before merging into the main production historical table (`tide_telemetry`).
* **📊 PowerBI-Themed Command UI (`static/` & `templates/`):** Dark-themed responsive interface built with `Orbitron` and `Rajdhani` typography, live digital clock, 15-minute auto-staging countdown ticker, Chart.js semidiurnal forecast horizon, and dynamic coastal environment simulation (Mahaul) viewports.

---

## 📁 Complete Project Directory Structure

```text
Tide-Prediction/
│
├── artifacts/                # Trained ML models, preprocessor, and split datasets
│   ├── preprocessor.pkl
│   ├── raw.csv
│   ├── test.csv
│   ├── train.csv
│   ├── testing_gate_model.joblib
│   └── tide_level_model.joblib
│
├── data/                     # Raw CSV datasets and SQLite production database
│   ├── chandipur_tide_1m_dataset.csv
│   └── pxe_portal.db
│
├── logs/                     # Application and execution logs
├── notebook/                 # Exploratory Data Analysis & training notebooks
│   └── 01_eda_and_model_training.ipynb
│
├── src/                      # Modular source package
│   ├── api/                  # External telemetry clients
│   │   ├── astronomy_client.py
│   │   └── weather_client.py
│   ├── components/           # Core pipeline blocks
│   │   ├── data_ingestion.py
│   │   ├── data_transformation.py
│   │   ├── merge_pipeline.py
│   │   └── model_trainer.py
│   ├── pipeline/             # Execution pipelines
│   │   ├── predict_pipeline.py
│   │   └── train_pipeline.py
│   ├── database.py           # SQLite connection & schema management
│   ├── exception.py          # Custom exception handling
│   ├── logger.py             # Centralized logging framework
│   └── utils.py              # Shared utility functions
│
├── static/                   # Frontend assets
│   ├── css/                  # Styling (style.css)
│   ├── images/               # Coastal simulation viewports (mudflat graphics)
│   └── js/                   # Dashboard logic & auto-staging timers (main.js)
│
├── templates/                # HTML UI layouts
│   └── index.html            # PowerBI command dashboard template
│
├── app.py                    # Flask web application main server & REST endpoints
├── manage_db.py              # Database maintenance & CLI utility tool
├── migrate_data.py           # Migration script for legacy telemetry data
├── requirements.txt          # Python package dependencies
├── setup.py                  # Package installation configuration
└── .gitignore                # Git exclusion rules