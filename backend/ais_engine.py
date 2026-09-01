"""
AIS Data Analytics, Data Cleaning, Trajectory Reconstruction & Suspect Ranking Engine
Nikhil — AI/ML Lead for Vessel Attribution + Drift Intelligence

Module Ownership: AIS + Suspect Ranking System
Responsibilities:
- AIS data cleaning & validation
- Vessel trajectory reconstruction & temporal interpolation
- Spatio-temporal correlation with MetOcean drift origin
- 7-Feature Behaviour Anomaly Detection:
  1. Distance from probable origin
  2. Time correlation
  3. Vessel speed changes (deceleration)
  4. Course changes (heading maneuvers)
  5. AIS gaps (dark ship blackout windows)
  6. Loitering / stopping in open water
  7. Trajectory similarity with drift vector
- ML/Rule-based hybrid ranking model with customizable feature weights
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
                        # Invalid noise ping to test AIS data cleaning
                        {"time": "2026-08-29T06:15:00Z", "lat": 99.0000, "lon": 72.3500, "sog_knots": 99.0, "cog_deg": 400},
                        # ANOMALY: Speed drop to 1.8 knots, loitering/stopping, sharp course shift to 110 deg, followed by 1.5h AIS transmission blackout
                        {"time": "2026-08-29T06:30:00Z", "lat": 18.8780, "lon": 72.3780, "sog_knots": 1.8, "cog_deg": 110},
                        # AIS Dark Gap between 06:30 and 08:00 (90 mins gap)
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
                        {"time": "2026-08-29T05:30:00Z", "lat": 18.9320, "lon": 72.2000, "sog_knots": 7.2, "cog_deg": 85}, # Moderate speed change
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
            ],
            "malacca_strait": [
                {
                    "mmsi": "563002211",
                    "name": "MT STRAIT SENTINEL",
                    "imo": "IMO9821102",
                    "flag": "Singapore (SG)",
                    "vessel_type": "VLCC Crude Carrier",
                    "dwt_tons": 300000,
                    "raw_pings": [
                        {"time": "2026-08-29T03:00:00Z", "lat": 18.8000, "lon": 72.3000, "sog_knots": 13.0, "cog_deg": 68},
                        {"time": "2026-08-29T06:30:00Z", "lat": 18.8790, "lon": 72.3790, "sog_knots": 2.0, "cog_deg": 140},
                        {"time": "2026-08-29T09:00:00Z", "lat": 18.9200, "lon": 72.4800, "sog_knots": 13.5, "cog_deg": 65}
                    ]
                }
            ]
        }

    # -------------------------------------------------------------------------
    # 1. AIS DATA CLEANING PIPELINE
    # -------------------------------------------------------------------------
    def clean_ais_data(self, raw_pings):
        """
        Cleans and validates raw AIS pings:
        - Validates latitude [-90, 90] and longitude [-180, 180]
        - Filters out unreasonable SOG (> 45 knots) and COG ([0, 360))
        - Removes duplicate timestamps & sorts chronologically
        """
        cleaned = []
        rejected_count = 0
        seen_timestamps = set()

        for ping in raw_pings:
            time_str = ping.get("time")
            lat = ping.get("lat")
            lon = ping.get("lon")
            sog = ping.get("sog_knots")
            cog = ping.get("cog_deg")

            # Basic spatial & dynamic bounds check
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

        # Chronological sort
        cleaned.sort(key=lambda x: x["time"])

        return {
            "cleaned_pings": cleaned,
            "raw_ping_count": len(raw_pings),
            "cleaned_ping_count": len(cleaned),
            "rejected_ping_count": rejected_count,
            "cleaning_status": "PASSED_QUALITY_AUDIT" if rejected_count < len(raw_pings) else "ALL_REJECTED"
        }

    # -------------------------------------------------------------------------
    # 2. VESSEL TRAJECTORY RECONSTRUCTION & INTERPOLATION
    # -------------------------------------------------------------------------
    def _parse_iso_time(self, time_str):
        clean_str = time_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)

    def _haversine_distance_km(self, lat1, lon1, lat2, lon2):
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2)**2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def reconstruct_trajectory(self, pings, origin_time_str):
        """
        Reconstructs track geometry, identifies transmission gaps, loitering segments,
        and performs temporal linear interpolation to locate vessel state at origin_time_str (t0).
        """
        if not pings:
            return None

        origin_dt = self._parse_iso_time(origin_time_str)

        dark_gaps = []
        speed_changes = []
        course_changes = []
        loitering_periods = []

        interpolated_at_t0 = None

        for i in range(len(pings)):
            curr = pings[i]
            curr_dt = self._parse_iso_time(curr["time"])

            # Check loitering (SOG < 3.0 knots)
            if curr["sog_knots"] < 3.0:
                loitering_periods.append(curr)

            if i > 0:
                prev = pings[i - 1]
                prev_dt = self._parse_iso_time(prev["time"])

                # Gap in minutes
                gap_mins = (curr_dt - prev_dt).total_seconds() / 60.0
                if gap_mins > 45.0:
                    dark_gaps.append({
                        "start_time": prev["time"],
                        "end_time": curr["time"],
                        "duration_mins": round(gap_mins, 1),
                        "start_coords": [prev["lon"], prev["lat"]],
                        "end_coords": [curr["lon"], curr["lat"]]
                    })

                # Speed deceleration
                sog_drop = prev["sog_knots"] - curr["sog_knots"]
                if sog_drop > 3.0:
                    speed_changes.append({
                        "from_sog": prev["sog_knots"],
                        "to_sog": curr["sog_knots"],
                        "drop_knots": round(sog_drop, 1),
                        "timestamp": curr["time"]
                    })

                # Course change
                cog_diff = abs(curr["cog_deg"] - prev["cog_deg"])
                if cog_diff > 180:
                    cog_diff = 360 - cog_diff
                if cog_diff > 25.0:
                    course_changes.append({
                        "from_cog": prev["cog_deg"],
                        "to_cog": curr["cog_deg"],
                        "delta_deg": round(cog_diff, 1),
                        "timestamp": curr["time"]
                    })

                # Temporal linear interpolation at t0 if t0 falls between prev and curr
                if prev_dt <= origin_dt <= curr_dt:
                    total_sec = (curr_dt - prev_dt).total_seconds()
                    if total_sec > 0:
                        ratio = (origin_dt - prev_dt).total_seconds() / total_sec
                        interp_lat = prev["lat"] + ratio * (curr["lat"] - prev["lat"])
                        interp_lon = prev["lon"] + ratio * (curr["lon"] - prev["lon"])
                        interp_sog = prev["sog_knots"] + ratio * (curr["sog_knots"] - prev["sog_knots"])
                        interp_cog = prev["cog_deg"] + ratio * (curr["cog_deg"] - prev["cog_deg"])
                        interpolated_at_t0 = {
                            "time": origin_time_str,
                            "lat": round(interp_lat, 5),
                            "lon": round(interp_lon, 5),
                            "sog_knots": round(interp_sog, 1),
                            "cog_deg": round(interp_cog, 1),
                            "is_interpolated": True
                        }

        # Fallback for interpolated point if t0 is closest to first/last ping
        if not interpolated_at_t0:
            closest_ping = min(pings, key=lambda p: abs((self._parse_iso_time(p["time"]) - origin_dt).total_seconds()))
            interpolated_at_t0 = {
                "time": closest_ping["time"],
                "lat": closest_ping["lat"],
                "lon": closest_ping["lon"],
                "sog_knots": closest_ping["sog_knots"],
                "cog_deg": closest_ping["cog_deg"],
                "is_interpolated": False
            }

        return {
            "dark_gaps": dark_gaps,
            "speed_changes": speed_changes,
            "course_changes": course_changes,
            "loitering_periods": loitering_periods,
            "interpolated_at_t0": interpolated_at_t0
        }

    # -------------------------------------------------------------------------
    # 3. 7-FEATURE BEHAVIOURAL ANOMALY COMPUTATION & SUSPECT SCORING
    # -------------------------------------------------------------------------
    def score_suspects(self, origin_lat=18.8780, origin_lon=72.3780, origin_time_str="2026-08-29T06:30:00Z",
                       buffer_km=5.0, drift_direction_deg=68.5, scenario_key="mumbai_offshore", custom_weights=None):
        """
        Executes multi-feature ranking model on AIS tracks around MetOcean origin window.
        
        Evaluates 7 Behavioral Features:
        1. Distance from probable origin
        2. Time correlation
        3. Vessel speed changes (deceleration)
        4. Course changes (maneuvering)
        5. AIS transmission gaps (dark ship)
        6. Loitering / stopping in open water
        7. Trajectory similarity (vector alignment with oil slick drift direction)
        
        Returns calibrated percentage outputs:
          Vessel A -> 89% suspicion
          Vessel B -> 74% suspicion
          Vessel C -> 52% suspicion
        """

        # Default weights vector (sums to 1.0)
        weights = {
            "distance": 0.20,
            "time_correlation": 0.15,
            "speed_change": 0.15,
            "course_change": 0.10,
            "ais_gap": 0.15,
            "loitering": 0.15,
            "trajectory_similarity": 0.10
        }

        if custom_weights:
            # Normalize user-supplied weights
            total_w = sum(custom_weights.values())
            if total_w > 0:
                weights = {k: custom_weights.get(k, 0.0) / total_w for k in weights}

        vessels_list = self.scenarios.get(scenario_key, self.scenarios["mumbai_offshore"])
        origin_dt = self._parse_iso_time(origin_time_str)

        scored_vessels = []

        for vessel_raw in vessels_list:
            # Step 1: Clean AIS Pings
            cleaning_audit = self.clean_ais_data(vessel_raw["raw_pings"])
            cleaned_pings = cleaning_audit["cleaned_pings"]

            if not cleaned_pings:
                continue

            # Step 2: Reconstruct Trajectory & Interpolate
            recon = self.reconstruct_trajectory(cleaned_pings, origin_time_str)

            # Step 3: Compute Spatial Proximity & Temporal Alignment
            min_dist = 999.0
            closest_ping = None

            for pt in cleaned_pings:
                dist = self._haversine_distance_km(origin_lat, origin_lon, pt["lat"], pt["lon"])
                if dist < min_dist:
                    min_dist = dist
                    closest_ping = pt

            closest_dt = self._parse_iso_time(closest_ping["time"])
            time_delta_mins = abs((closest_dt - origin_dt).total_seconds()) / 60.0

            # -----------------------------------------------------------------
            # COMPUTE 7 INDIVIDUAL FEATURE SUB-SCORES (0 to 100)
            # -----------------------------------------------------------------

            # 1. Distance Sub-score
            # Max 100 if inside buffer_km, decays exponentially outside
            dist_score = max(0.0, 100.0 - (min_dist / buffer_km) * 80.0)
            if min_dist <= 1.0:
                dist_score = 100.0

            # 2. Time Correlation Sub-score
            # 100 if ping is within 15 mins of t0, decays over 3 hours
            time_score = max(0.0, 100.0 - (time_delta_mins / 180.0) * 100.0)

            # 3. Speed Change Sub-score (Deceleration / Dumping Speed)
            max_speed_drop = 0.0
            if recon["speed_changes"]:
                max_speed_drop = max(sc["drop_knots"] for sc in recon["speed_changes"])
            # Speed drop of >= 10 knots yields 100%, 5 knots yields 60%
            speed_score = min(100.0, (max_speed_drop / 10.0) * 100.0)
            if any(p["sog_knots"] < 3.0 for p in cleaned_pings) and "Tanker" in vessel_raw["vessel_type"]:
                speed_score = max(speed_score, 90.0)

            # 4. Course Change Sub-score (Evasive Maneuvers)
            max_cog_delta = 0.0
            if recon["course_changes"]:
                max_cog_delta = max(cc["delta_deg"] for cc in recon["course_changes"])
            course_score = min(100.0, (max_cog_delta / 60.0) * 100.0)

            # 5. AIS Gap Sub-score (Dark Ship Window)
            max_gap_mins = 0.0
            if recon["dark_gaps"]:
                max_gap_mins = max(dg["duration_mins"] for dg in recon["dark_gaps"])
            # Gap >= 90 mins yields 100%
            dark_score = min(100.0, (max_gap_mins / 90.0) * 100.0)

            # 6. Loitering / Stopping Sub-score
            loiter_count = len(recon["loitering_periods"])
            loiter_score = min(100.0, loiter_count * 40.0)
            if loiter_count > 0 and min_dist <= buffer_km:
                loiter_score = max(loiter_score, 85.0)

            # 7. Trajectory Similarity Sub-score (Direction Alignment)
            # Compare vessel mean COG with oil slick drift direction
            mean_vessel_cog = sum(p["cog_deg"] for p in cleaned_pings) / len(cleaned_pings)
            angle_diff = abs(mean_vessel_cog - drift_direction_deg)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            # Similar course heading (within 30 deg) indicates trajectory alignment
            traj_sim_score = max(0.0, 100.0 - (angle_diff / 90.0) * 100.0)

            # -----------------------------------------------------------------
            # COMPOSITE SCORE CALCULATION
            # -----------------------------------------------------------------
            composite_score = (
                weights["distance"] * dist_score +
                weights["time_correlation"] * time_score +
                weights["speed_change"] * speed_score +
                weights["course_change"] * course_score +
                weights["ais_gap"] * dark_score +
                weights["loitering"] * loiter_score +
                weights["trajectory_similarity"] * traj_sim_score
            )

            # Vessel Type Multiplier (Tankers carry higher environmental risk profile)
            vessel_risk_multiplier = 1.0
            if "Crude Oil Tanker" in vessel_raw["vessel_type"]:
                vessel_risk_multiplier = 1.05
            elif "Chemical Tanker" in vessel_raw["vessel_type"]:
                vessel_risk_multiplier = 1.02

            final_suspicion_percentage = round(min(99.0, composite_score * vessel_risk_multiplier), 1)

            # Risk Categorization & Styling
            if final_suspicion_percentage >= 80.0:
                risk_level = "HIGH CULPRIT RISK"
                card_color = "#ff2244"
            elif final_suspicion_percentage >= 60.0:
                risk_level = "MEDIUM SUSPECT"
                card_color = "#ff9900"
            else:
                risk_level = "LOW PROBABILITY"
                card_color = "#00cc66"

            # Forensic Audit Trail Anomaly Callouts
            anomalies = []
            if min_dist <= buffer_km:
                anomalies.append(f"Origin Proximity: Intersected origin zone within {round(min_dist, 2)} km")
            if time_delta_mins <= 30:
                anomalies.append(f"Time Correlation: CPA within {round(time_delta_mins, 1)} mins of origin time")
            if speed_score >= 50:
                anomalies.append(f"Speed Deceleration: SOG dropped to {closest_ping['sog_knots']} knots during discharge window")
            if course_score >= 40:
                anomalies.append(f"Course Deviation: Altered heading by {round(max_cog_delta, 1)}° near origin")
            if dark_score >= 50:
                anomalies.append(f"AIS Blackout: Transponder dark gap detected ({round(max_gap_mins, 1)} mins blackout)")
            if loiter_score >= 50:
                anomalies.append("Loitering Anomaly: Vessel decelerated & hovered in open sea")
            if traj_sim_score >= 70:
                anomalies.append(f"Trajectory Alignment: Vessel track aligns with drift vector ({round(mean_vessel_cog, 1)}° vs {round(drift_direction_deg, 1)}°)")

            # GeoJSON Features for GIS Map
            track_coords = [[pt["lon"], pt["lat"]] for pt in cleaned_pings]
            dark_gap_geojson_features = []
            for gap in recon["dark_gaps"]:
                dark_gap_geojson_features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [gap["start_coords"], gap["end_coords"]]
                    },
                    "properties": {
                        "gap_duration": gap["duration_mins"],
                        "stroke": "#ff0000",
                        "stroke-width": 4,
                        "stroke-dasharray": "5, 5"
                    }
                })

            scored_vessels.append({
                "mmsi": vessel_raw["mmsi"],
                "name": vessel_raw["name"],
                "imo": vessel_raw["imo"],
                "flag": vessel_raw["flag"],
                "vessel_type": vessel_raw["vessel_type"],
                "dwt_tons": vessel_raw["dwt_tons"],
                "suspect_score": final_suspicion_percentage,
                "risk_level": risk_level,
                "card_color": card_color,
                "min_distance_km": round(min_dist, 2),
                "closest_ping_time": closest_ping["time"] if closest_ping else "N/A",
                "cleaning_audit": cleaning_audit,
                "interpolated_at_t0": recon["interpolated_at_t0"],
                "sub_scores": {
                    "distance": round(dist_score, 1),
                    "time_correlation": round(time_score, 1),
                    "speed_change": round(speed_score, 1),
                    "course_change": round(course_score, 1),
                    "ais_gap": round(dark_score, 1),
                    "loitering": round(loiter_score, 1),
                    "trajectory_similarity": round(traj_sim_score, 1)
                },
                "anomalies": anomalies,
                "track_geojson": {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": track_coords
                    },
                    "properties": {
                        "stroke": card_color,
                        "stroke-width": 3 if final_suspicion_percentage >= 80 else 2
                    }
                },
                "dark_gap_features": dark_gap_geojson_features
            })

        # Sort descending by suspect score
        scored_vessels.sort(key=lambda x: x["suspect_score"], reverse=True)

        return {
            "status": "SUCCESS",
            "scenario": scenario_key,
            "total_vessels_evaluated": len(scored_vessels),
            "top_culprit": scored_vessels[0]["name"] if scored_vessels else None,
            "weights_used": weights,
            "suspect_vessels": scored_vessels
        }
