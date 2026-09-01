"""
Integration test for Nikhil's FastAPI endpoints:
AIS Cleaning, Trajectory Reconstruction, MetOcean Hindcasting, 7-Feature Suspect Scoring & Forensic Report
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ONLINE")
        self.assertIn("Nikhil", res.json()["owner"])

    def test_ais_cleaning_endpoint(self):
        raw_pings = [
            {"time": "2026-08-29T05:00:00Z", "lat": 18.8200, "lon": 72.2500, "sog_knots": 14.2, "cog_deg": 65},
            {"time": "2026-08-29T06:15:00Z", "lat": 99.0000, "lon": 72.3500, "sog_knots": 99.0, "cog_deg": 400},
            {"time": "2026-08-29T06:00:00Z", "lat": 18.8500, "lon": 72.3200, "sog_knots": 13.8, "cog_deg": 64}
        ]
        res = self.client.post("/api/clean-ais", json={"raw_pings": raw_pings})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["cleaned_ping_count"], 2)
        self.assertEqual(data["rejected_ping_count"], 1)

    def test_hindcast_and_score_vessels_flow(self):
        # 1. Hindcast drift
        res_drift = self.client.post("/api/hindcast", json={"lat": 18.9200, "lon": 72.4500, "hours_back": 7.5})
        self.assertEqual(res_drift.status_code, 200)
        drift_data = res_drift.json()
        self.assertEqual(drift_data["status"], "SUCCESS")

        # 2. Score vessels
        res_score = self.client.post("/api/score-vessels", json={"scenario": "mumbai_offshore"})
        self.assertEqual(res_score.status_code, 200)
        score_data = res_score.json()
        self.assertEqual(score_data["status"], "SUCCESS")
        self.assertEqual(score_data["top_culprit"], "MV OCEAN PRINCE")

        # Top culprit verification
        top = score_data["suspect_vessels"][0]
        self.assertEqual(top["name"], "MV OCEAN PRINCE")
        self.assertGreaterEqual(top["suspect_score"], 80.0)

        # 3. Incident report
        res_report = self.client.get("/api/report")
        self.assertEqual(res_report.status_code, 200)
        report = res_report.json()
        self.assertIn("report_id", report)
        self.assertEqual(report["primary_culprit_vessel"]["name"], "MV OCEAN PRINCE")

    def test_custom_weight_scoring_endpoint(self):
        payload = {
            "scenario": "mumbai_offshore",
            "weights": {
                "distance": 30,
                "time_correlation": 20,
                "speed_change": 20,
                "course_change": 10,
                "ais_gap": 10,
                "loitering": 5,
                "trajectory_similarity": 5
            }
        }
        res = self.client.post("/api/score-vessels", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("weights_used", data)

if __name__ == "__main__":
    unittest.main()
