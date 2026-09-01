"""
AIS Data Analytics, Data Cleaning, Trajectory Reconstruction & Suspect Ranking Engine
Nikhil — AI/ML Lead for Vessel Attribution + Drift Intelligence
"""

import math
from datetime import datetime, timezone

class AISEngine:
    def __init__(self):
        # Scenario 1: Default - Mumbai Offshore / Arabian Sea Corridor
        self.scenarios = {
            "mumbai_offshore": [
                {
                    "mmsi": "419001234",
                    "name": "MV OCEAN PRINCE",
                    "imo": "IMO9348571",
                    "flag": "Panama (PA)",
                    "vessel_type": "Crude Oil Tanker",
                    "dwt_tons": 115000,
                    "raw_pings": [
                        {"time": "2026-08-29T05:00:00Z", "lat": 18.8200, "lon": 72.2500, "sog_knots": 14.2, "cog_deg": 65},
                        {"time": "2026-08-29T06:00:00Z", "lat": 18.8500, "lon": 72.3200, "sog_knots": 13.8, "cog_deg": 64},
                        {"time": "2026-08-29T06:15:00Z", "lat": 99.0000, "lon": 72.3500, "sog_knots": 99.0, "cog_deg": 400},
                        {"time": "2026-08-29T06:30:00Z", "lat": 18.8780, "lon": 72.3780, "sog_knots": 1.8, "cog_deg": 110},
                        {"time": "2026-08-29T08:00:00Z", "lat": 18.8890, "lon": 72.4100, "sog_knots": 13.9, "cog_deg": 62},
                        {"time": "2026-08-29T10:00:00Z", "lat": 18.9100, "lon": 72.4600, "sog_knots": 14.1, "cog_deg": 65},
                        {"time": "2026-08-29T14:00:00Z", "lat": 18.9500, "lon": 72.5500, "sog_knots": 14.0, "cog_deg": 65}
                    ]
                },
                {
                    "mmsi": "419009999",
                    "name": "MV ARABIAN BREEZE",
                    "imo": "IMO9204857",
                    "flag": "Marshall Islands (MH)",
                    "vessel_type": "Chemical Tanker",
                    "dwt_tons": 45000,
                    "raw_pings": [
                        {"time": "2026-08-29T04:00:00Z", "lat": 18.9200, "lon": 72.1000, "sog_knots": 11.5, "cog_deg": 70},
                        {"time": "2026-08-29T05:30:00Z", "lat": 18.9320, "lon": 72.2000, "sog_knots": 7.2, "cog_deg": 85},
                        {"time": "2026-08-29T06:15:00Z", "lat": 18.9400, "lon": 72.2800, "sog_knots": 6.5, "cog_deg": 70},
                        {"time": "2026-08-29T08:30:00Z", "lat": 18.9600, "lon": 72.4800, "sog_knots": 11.0, "cog_deg": 70}
                    ]
                },
                {
                    "mmsi": "419005678",
                    "name": "MV PACIFIC STAR",
                    "imo": "IMO9412093",
                    "flag": "Liberia (LR)",
                    "vessel_type": "Container Ship",
                    "dwt_tons": 68000,
                    "raw_pings": [
                        {"time": "2026-08-29T05:30:00Z", "lat": 18.7500, "lon": 72.2000, "sog_knots": 18.5, "cog_deg": 58},
                        {"time": "2026-08-29T06:30:00Z", "lat": 18.8100, "lon": 72.3300, "sog_knots": 18.2, "cog_deg": 58},
                        {"time": "2026-08-29T07:30:00Z", "lat": 18.8700, "lon": 72.4500, "sog_knots": 18.0, "cog_deg": 58},
                        {"time": "2026-08-29T09:30:00Z", "lat": 18.9800, "lon": 72.6500, "sog_knots": 18.1, "cog_deg": 58}
                    ]
                }
            ]
        }
