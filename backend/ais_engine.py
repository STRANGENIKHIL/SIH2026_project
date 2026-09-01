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

    def clean_ais_data(self, raw_pings):
        """Cleans and validates raw AIS pings filtering spatial, speed & heading outliers."""
        cleaned = []
        rejected_count = 0
        seen_timestamps = set()

        for ping in raw_pings:
            time_str = ping.get("time")
            lat = ping.get("lat")
            lon = ping.get("lon")
            sog = ping.get("sog_knots")
            cog = ping.get("cog_deg")

            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                rejected_count += 1
                continue
            if not (0.0 <= sog <= 45.0):
                rejected_count += 1
                continue
            if not (0.0 <= cog <= 360.0):
                rejected_count += 1
                continue
            if time_str in seen_timestamps:
                rejected_count += 1
                continue

            seen_timestamps.add(time_str)
            cleaned.append(ping)

        cleaned.sort(key=lambda x: x["time"])
        return {
            "cleaned_pings": cleaned,
            "raw_ping_count": len(raw_pings),
            "cleaned_ping_count": len(cleaned),
            "rejected_ping_count": rejected_count,
            "cleaning_status": "PASSED_QUALITY_AUDIT" if rejected_count < len(raw_pings) else "ALL_REJECTED"
        }
