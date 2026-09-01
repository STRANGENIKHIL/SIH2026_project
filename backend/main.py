"""
FastAPI Server & Route Handlers for Nikhil's Module (SIH PS 26143)
AIS Data Analytics, Vessel Trajectory Reconstruction, 7-Feature Anomaly Scoring & MetOcean Drift Intelligence
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.drift_engine import DriftSimulator
from backend.ais_engine import AISEngine
from backend.pdf_generator import ForensicReportGenerator

app = FastAPI(
    title="AIS Vessel Attribution & Drift Intelligence Platform",
    description="Nikhil's Module: AIS Cleaning, Trajectory Reconstruction, 7-Feature Anomaly Detection, Suspect Vessel Scoring & MetOcean Hindcasting Engine",
    version="1.0.0"
)

# Enable CORS for frontend integration (Krishu's React Dashboard & Aditya's Mapbox/Leaflet UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Processing Engines
drift_sim = DriftSimulator()
ais_engine = AISEngine()
pdf_exporter = ForensicReportGenerator()

# In-memory session state
state = {
    "origin": {"lat": 18.8780, "lon": 72.3780, "time": "2026-08-29T06:30:00Z"},
    "drift": None,
    "ais_scoring": None
}

class OriginRequest(BaseModel):
    lat: float = Field(default=18.9200, description="Spill detection centroid latitude")
    lon: float = Field(default=72.4500, description="Spill detection centroid longitude")
    hours_back: float = Field(default=7.5, description="Hindcast hours back to origin t0")

class AISCleanRequest(BaseModel):
    raw_pings: List[Dict[str, Any]]

class TrajectoryRequest(BaseModel):
    pings: List[Dict[str, Any]]
    origin_time_str: str = "2026-08-29T06:30:00Z"

class AISScoringRequest(BaseModel):
    origin_lat: float = 18.8780
    origin_lon: float = 72.3780
    origin_time_str: str = "2026-08-29T06:30:00Z"
    buffer_km: float = 5.0
    drift_direction_deg: float = 68.5
    scenario: Optional[str] = "mumbai_offshore"
    weights: Optional[Dict[str, float]] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "ONLINE",
        "system": "Nikhil — AIS Vessel Attribution & Drift Intelligence Engine",
        "version": "1.0.0",
        "owner": "Nikhil (AI/ML Lead for Vessel Attribution + Drift Intelligence)",
        "modules": [
            "AIS Data Cleaning & Validation",
            "Vessel Trajectory Reconstruction & Interpolation",
            "MetOcean Lagrangian Drift Hindcasting Engine",
            "7-Feature Behavioral Anomaly Detection Engine",
            "Hybrid ML/Rule Suspect Ranking & Attribution Model"
        ]
    }

@app.post("/api/clean-ais")
def clean_ais_data(req: AISCleanRequest):
    """Clean & validate raw AIS pings (filters spatial noise, extreme SOG, invalid COG, duplicates)."""
    try:
        return ais_engine.clean_ais_data(req.raw_pings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reconstruct-trajectory")
def reconstruct_trajectory(req: TrajectoryRequest):
    """Reconstruct vessel track geometry, identify loitering, dark ship gaps, and interpolate state at t0."""
    try:
        return ais_engine.reconstruct_trajectory(req.pings, req.origin_time_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hindcast")
def run_hindcast(req: Optional[OriginRequest] = None):
    """Runs Lagrangian particle drift backward to locate spill origin window (t0, x0, y0) and forward forecast."""
    try:
        lat = req.lat if req else 18.9200
        lon = req.lon if req else 72.4500
        hours_back = req.hours_back if req else 7.5

        drift_result = drift_sim.run_hindcast(lat, lon, hours_back=hours_back)
        forecast_result = drift_sim.run_forecast(lat, lon, hours_forward=48)
        
        drift_result["forecast_geojson"] = forecast_result
        state["drift"] = drift_result
        state["origin"] = {
            "lat": drift_result["origin_centroid"]["lat"],
            "lon": drift_result["origin_centroid"]["lon"],
            "time": drift_result["estimated_origin_time"]
        }
        return drift_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/score-vessels")
def score_vessels(req: Optional[AISScoringRequest] = None):
    """
    Evaluates Candidate Vessel Tracks around MetOcean origin window using Nikhil's 7-Feature Anomaly Model:
    1. Distance from probable origin
    2. Time correlation
    3. Speed changes (deceleration)
    4. Course changes (heading maneuvers)
    5. AIS gaps (dark ship blackout windows)
    6. Loitering / stopping in open water
    7. Trajectory similarity with drift bearing
    """
    try:
        if not state["drift"]:
            run_hindcast()

        origin_lat = req.origin_lat if (req and req.origin_lat) else state["origin"]["lat"]
        origin_lon = req.origin_lon if (req and req.origin_lon) else state["origin"]["lon"]
        origin_time = req.origin_time_str if (req and req.origin_time_str) else state["origin"]["time"]
        buffer_km = req.buffer_km if (req and req.buffer_km) else state["drift"]["uncertainty_radius_km"]
        drift_dir = req.drift_direction_deg if (req and req.drift_direction_deg) else state["drift"]["metocean_summary"]["drift_direction_deg"]
        scenario = req.scenario if (req and req.scenario) else "mumbai_offshore"
        weights = req.weights if (req and req.weights) else None

        ais_result = ais_engine.score_suspects(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            origin_time_str=origin_time,
            buffer_km=buffer_km,
            drift_direction_deg=drift_dir,
            scenario_key=scenario,
            custom_weights=weights
        )
        state["ais_scoring"] = ais_result
        return ais_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report")
def get_incident_report():
    """Generates official forensic evidence report summary for primary suspect vessel."""
    if not (state["drift"] and state["ais_scoring"]):
        run_hindcast()
        score_vessels()
        
    detection_mock = {
        "sensor": "Sentinel-1B SAR C-Band",
        "detection_timestamp": "2026-08-29T14:00:00Z",
        "centroid": {"lat": 18.9200, "lon": 72.4500},
        "characterization": {
            "surface_area_km2": 14.85,
            "estimated_volume_m3": 7425.0,
            "classification": "Heavy Fuel Oil (HFO) / Bilge Waste Discharge"
        }
    }

    report = pdf_exporter.generate_incident_report(
        detection_mock,
        state["drift"],
        state["ais_scoring"]
    )
    return report
