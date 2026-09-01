# 🚢 AIS Vessel Attribution & Spatio-Temporal Drift Intelligence Engine

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![SIH PS 26143](https://img.shields.io/badge/SIH%20PS-26143-orange.svg)](https://sih.gov.in)

> **Module Lead**: **Nikhil** — *AI/ML Lead for Vessel Attribution + Drift Intelligence*  
> **Project**: Smart India Hackathon (SIH 2026) - NTRO Maritime Oil Spill Attribution (PS 26143)

---

## 👥 Team Workload & Module Ownership Breakdown

| Team Member | Domain / Module | Primary Responsibilities |
| :--- | :--- | :--- |
| **Nikhil** *(This Repo)* | **AIS + Suspect Ranking + Drift Intelligence** | AIS Data Cleaning, Trajectory Reconstruction, Spatio-Temporal Correlation, 7-Feature Anomaly Detection, Suspect Vessel Scoring & MetOcean Hindcasting Engine |
| **Arham** | **Computer Vision / Oil Spill AI** | SAR Dataset Preparation, Image Preprocessing, U-Net / DeepLabV3 Segmentation Model, Slick Geometry Mask Extraction & Confidence Scoring |
| **Krishu** | **Frontend Lead + Dashboard UI/UX** | React Frontend Architecture, Main Command Dashboard UI/UX, Analytics Panels, Charts & Time Control Components |
| **Aditya** | **Geospatial Visualization & Map Intelligence** | Leaflet / Mapbox GIS Integration, Satellite Layer Rendering, Oil Spill Polygon Overlays, AIS Vessel Animation Tracks & Drift Paths |

---

## 🎯 Nikhil's Module Overview & Architecture

Nikhil's module provides the high-performance AI/ML engine for **cleaning AIS ship tracking data**, **reconstructing vessel trajectories**, **computing Lagrangian MetOcean drift backward to origin ($t_0$)**, and **scoring suspect vessels across 7 behavioral anomaly vectors**.

```
                           ┌────────────────────────────────────────┐
                           │   Input: Candidate AIS Ship Feeds      │
                           └────────────────────────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │     1. AIS Data Cleaning & Quality     │
                           │  (Filters noise, bad lat/lon, SOG/COG)  │
                           └────────────────────────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │   2. Vessel Trajectory Reconstruction   │
                           │     (Dark gaps, loitering, interp t₀)  │
                           └────────────────────────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │    3. MetOcean Drift Hindcast (t₀)     │
                           │    (HYCOM ocean current + ERA5 wind)   │
                           └────────────────────────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │ 4. 7-Feature Behavioral Anomaly Model  │
                           │  - Distance from origin    - AIS gap   │
                           │  - Time correlation        - Loiter    │
                           │  - Deceleration (SOG)      - Traj sim  │
                           │  - Heading maneuvers (COG)             │
                           └────────────────────────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │    5. Suspect Vessel Ranking Output    │
                           │     Vessel A ──> 89% Suspicion         │
                           │     Vessel B ──> 74% Suspicion         │
                           │     Vessel C ──> 52% Suspicion         │
                           └────────────────────────────────────────┘
```

---

## 📊 7-Feature Behavioral Anomaly Detection Model

Candidate vessels inside the MetOcean origin uncertainty zone are evaluated using a calibrated multi-feature scoring model:

1. **Origin Distance Proximity**: Spatial distance ($km$) between vessel track and calculated spill origin centroid $(x_0, y_0)$.
2. **Time Correlation**: Temporal delta ($mins$) between vessel passage and estimated discharge time ($t_0$).
3. **Speed Deceleration (Discharge Speed)**: SOG drop below 3.0 knots during transit, characteristic of bilge/slop discharge maneuvers.
4. **Course Maneuvering ($\Delta$ COG)**: Sharp heading alterations ($> 25^\circ$) near origin zone.
5. **AIS Blackout Gap (Dark Ship Window)**: Transponder disconnections or signal transmission gaps ($> 45$ mins).
6. **Open-Sea Loitering**: Unscheduled deceleration or hovering in international shipping channels.
7. **Trajectory Similarity**: Directional vector alignment between vessel heading and MetOcean drift bearing.

### Example Output:
- **Vessel A** (`MV OCEAN PRINCE`): **89.2%** Suspicion (*High Culprit Risk — SOG drop to 1.8 kts, 90-min dark gap, origin intersection*)
- **Vessel B** (`MV ARABIAN BREEZE`): **74.1%** Suspicion (*Medium Suspect — Moderate deceleration & course change*)
- **Vessel C** (`MV PACIFIC STAR`): **52.4%** Suspicion (*Low Risk — Consistent speed & transit route*)

---

## 📁 Repository File Layout

```
.
├── app.py                      # Module Launcher (starts FastAPI service)
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI API Endpoint Handlers for Nikhil's Service
│   ├── ais_engine.py           # Core AIS Data Cleaning, Trajectory Recon & 7-Feature Model
│   ├── drift_engine.py         # MetOcean Lagrangian Backward/Forward Drift Physics Tracker
│   └── pdf_generator.py        # Legal Forensic Audit Evidence Exporter Summary
├── tests/
│   ├── test_ais_engine.py             # Unit Tests for AIS Cleaning & Anomaly Scoring
│   └── test_pipeline_integration.py   # FastAPI Endpoint Integration Tests
├── requirements.txt            # Python Dependencies
├── .gitignore                  # Git Ignore Config
└── README.md                   # System Documentation
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Nikhil's API Service
```bash
python app.py
```
*Service starts on `http://127.0.0.1:8000`. Access Swagger UI docs at `http://127.0.0.1:8000/docs`.*

### 3. Run Test Suite
```bash
python -m pytest
```

---

## 📡 API Integration for Team Members

Arham (CV), Krishu (React UI), and Aditya (Mapbox/GIS) consume these API endpoints:

| Endpoint | Method | Input Payload / Parameters | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | None | Service status & module ownership metadata |
| `/api/clean-ais` | `POST` | `{"raw_pings": [...]}` | Filters spatial/dynamic noise & returns clean chronological AIS pings |
| `/api/reconstruct-trajectory` | `POST` | `{"pings": [...], "origin_time_str": "ISO"}` | Reconstructs track geometry, loitering, dark gaps & $t_0$ interpolation |
| `/api/hindcast` | `POST` | `{"lat": 18.92, "lon": 72.45, "hours_back": 7.5}` | Runs MetOcean backward drift to find origin $(x_0, y_0, t_0)$ & forecast |
| `/api/score-vessels` | `POST` | `{"scenario": "mumbai_offshore", "weights": {...}}` | Scores suspect vessels using Nikhil's 7-feature model & custom weights |
| `/api/report` | `GET` | None | Returns official legal evidence audit summary for primary suspect |

---

## 📜 License & Attribution

Developed by **Nikhil** (*AI/ML Lead for Vessel Attribution + Drift Intelligence*) for **Smart India Hackathon 2026 (SIH PS 26143 - NTRO)**.
