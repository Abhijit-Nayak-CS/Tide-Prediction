# 🛡️ DRDO PXE Chandipur - Coastal Defense & Mission Portal

> **Autonomous Intertidal Mudflat Prediction, Weapon Testing & Range Clearance Portal** developed for Proof & Experimental Establishment (PXE), Chandipur.

---

## 📋 About The Project
The **DRDO PXE Coastal Defense & Mission Portal** is an advanced, PowerBI-inspired command-and-control web application designed to monitor intertidal mudflat conditions, predict dynamic sea tide levels, and evaluate real-time range safety for weapon testing and tracking operations off the coast of Chandipur, Odisha.

Chandipur's unique geographical phenomenon—where the sea recedes up to 5 kilometers during low tide—creates vast compacted mudflat corridors. This portal bridges meteorological, astronomical, and physics-based telemetry to provide automated mission clearance and risk assessment for range safety officers (RSOs).

---

## ✨ Key Features & Capabilities

* **🧠 Machine Learning & Physics Hybrid Engine:** Integrates trained **LightGBM Regressor** and **Classifier** models alongside custom semidiurnal physics formulas to predict precise sea levels, exposure distances, and firing gate safety.
* **🌐 Real-Time Telemetry & API Integration:** Fetches live atmospheric data (wind speed, direction, temperature, pressure, humidity, and optical visibility) via the OpenWeatherMap API with a robust double-tier database and mathematical fallback mechanism.
* **🔭 High-Precision Astronomical Calculations:** Computes real-time lunar phases, moon distances, and gravitational tidal modulations using the `ephem` library.
* **📍 Spatial Stump Submersion Profile:** Monitors real-time water depth across critical seabed boundary markers ranging from **50m to 1000m seaward**.
* **⏱️ Automated Staging & 15-Minute Logger:** Features an automated telemetry logging loop with a live visual MM:SS countdown and strict duplicate-prevention locks (frontend & backend level).
* **🔄 Staging-to-Production Pipeline:** Implements a two-tier database workflow (`staging_telemetry` $\rightarrow$ `tide_telemetry`) with secure cryptographic commit hashes (`PXE-CMT-xxxx`) before merging into the main historical database.
* **📊 PowerBI-Themed Dark UI:** Command-center aesthetic utilizing `Orbitron` and `Rajdhani` typography, interactive Chart.js horizon graphs, and dynamic range clearance banners (`CLEAR`, `WARNING`, `RESTRICTED`).

---

## 🛠️ Tech Stack & Architecture

* **Backend:** Python, Flask, Gunicorn
* **Machine Learning & Data Science:** LightGBM, Scikit-Learn, Pandas, NumPy, Joblib, Ephem
* **Database:** SQLite3 (Modular schema with Staging & Production pipelines)
* **Frontend:** HTML5, CSS3, JavaScript (ES6+), Chart.js, FontAwesome
* **DevOps & Tools:** Git, GitHub, Docker-ready modular structure

---

## 📁 Project Directory Structure

```text
PXE_Tide_Portal/
│
├── artifacts/                # Trained LightGBM model binaries (.joblib)
├── src/                      # Modular source package
│   ├── api/                  # OpenWeatherMap & Astronomy telemetry clients
│   ├── components/           # Data transformation, seabed elevations & merge pipelines
│   ├── pipeline/             # Prediction & training execution modules
│   ├── database.py           # SQLite connection and schema management
│   ├── exception.py          # Custom error handling framework
│   └── logger.py             # Centralized logging configuration
│
├── static/                   # Frontend assets (CSS stylesheets, JS modules, images)
├── templates/                # HTML interface templates (index.html)
├── app.py                    # Flask web application main server & REST API endpoints
├── manage_db.py              # Database management & CLI utility tool
├── setup.py                  # Package installation configuration
└── requirements.txt          # Project dependencies
