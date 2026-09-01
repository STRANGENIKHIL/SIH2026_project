"""
Forensic Audit Report & Evidence Exporter Module
Generates structured incident reports containing SAR detection parameters,
MetOcean hindcast trajectory data, and suspect vessel evidence trail.
"""

from datetime import datetime

class ForensicReportGenerator:
    def generate_incident_report(self, detection_data, drift_data, suspect_data):
        top_culprit = suspect_data["suspect_vessels"][0] if suspect_data.get("suspect_vessels") else {}

        report_summary = {
            "report_id": f"NTRO-SPILL-2026-{datetime.now().strftime('%m%d%H%M')}",
            "generated_at": datetime.now().isoformat() + "Z",
            "organization": "National Technical Research Organisation (NTRO)",
            "classification": "RESTRICTED / MARITIME EVIDENCE",
            "spill_incident": {
                "sensor": detection_data["sensor"],
                "detection_time": detection_data["detection_timestamp"],
                "surface_area_km2": detection_data["characterization"]["surface_area_km2"],
                "estimated_volume_m3": detection_data["characterization"]["estimated_volume_m3"],
                "classification": detection_data["characterization"]["classification"],
                "centroid": detection_data["centroid"]
            },
            "hindcast_drift": {
                "estimated_origin_time": drift_data["estimated_origin_time"],
                "origin_centroid": drift_data["origin_centroid"],
                "uncertainty_radius_km": drift_data["uncertainty_radius_km"],
                "drift_direction_deg": drift_data["metocean_summary"]["drift_direction_deg"]
            },
            "primary_culprit_vessel": {
                "name": top_culprit.get("name"),
                "mmsi": top_culprit.get("mmsi"),
                "imo": top_culprit.get("imo"),
                "flag": top_culprit.get("flag"),
                "type": top_culprit.get("vessel_type"),
                "culprit_match_score": f"{top_culprit.get('suspect_score')}%",
                "risk_level": top_culprit.get("risk_level"),
                "sub_scores": top_culprit.get("sub_scores", {}),
                "cleaning_audit": top_culprit.get("cleaning_audit", {}),
                "interpolated_at_t0": top_culprit.get("interpolated_at_t0", {}),
                "detected_anomalies": top_culprit.get("anomalies", [])
            },
            "total_vessels_evaluated": suspect_data.get("total_vessels_evaluated", 0),
            "ranking_model": "NTRO Multi-Feature ML/Rule Ensemble (7 Anomaly Vector Model)"
        }
        return report_summary
