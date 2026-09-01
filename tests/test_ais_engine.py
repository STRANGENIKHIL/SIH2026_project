"""
Unit Tests for Nikhil's AIS Data Cleaning, Trajectory Reconstruction, and 7-Feature Suspect Ranking System.
"""

import sys
import os
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ais_engine import AISEngine

class TestAISEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AISEngine()

    def test_ais_data_cleaning(self):
        raw_pings = [
            {"time": "2026-08-29T05:00:00Z", "lat": 18.8200, "lon": 72.2500, "sog_knots": 14.2, "cog_deg": 65},
            {"time": "2026-08-29T06:15:00Z", "lat": 99.0000, "lon": 72.3500, "sog_knots": 99.0, "cog_deg": 400}, # Outlier ping
            {"time": "2026-08-29T06:00:00Z", "lat": 18.8500, "lon": 72.3200, "sog_knots": 13.8, "cog_deg": 64}
        ]

        audit = self.engine.clean_ais_data(raw_pings)
        self.assertEqual(audit["raw_ping_count"], 3)
        self.assertEqual(audit["cleaned_ping_count"], 2)
        self.assertEqual(audit["rejected_ping_count"], 1)

        # Check chronological order
        cleaned = audit["cleaned_pings"]
        self.assertEqual(cleaned[0]["time"], "2026-08-29T05:00:00Z")
        self.assertEqual(cleaned[1]["time"], "2026-08-29T06:00:00Z")

    def test_trajectory_reconstruction_and_interpolation(self):
        pings = [
            {"time": "2026-08-29T06:00:00Z", "lat": 18.8200, "lon": 72.2500, "sog_knots": 14.0, "cog_deg": 65},
            {"time": "2026-08-29T06:30:00Z", "lat": 18.8800, "lon": 72.3800, "sog_knots": 2.0, "cog_deg": 110},
            {"time": "2026-08-29T08:00:00Z", "lat": 18.9000, "lon": 72.4200, "sog_knots": 14.0, "cog_deg": 65} # 90 min gap
        ]

        recon = self.engine.reconstruct_trajectory(pings, origin_time_str="2026-08-29T06:30:00Z")
        self.assertIsNotNone(recon["interpolated_at_t0"])
        self.assertEqual(recon["interpolated_at_t0"]["lat"], 18.8800)
        self.assertEqual(len(recon["dark_gaps"]), 1)
        self.assertEqual(recon["dark_gaps"][0]["duration_mins"], 90.0)

    def test_score_suspects_7_features(self):
        result = self.engine.score_suspects(
            origin_lat=18.8780,
            origin_lon=72.3780,
            origin_time_str="2026-08-29T06:30:00Z",
            buffer_km=5.0,
            drift_direction_deg=68.5,
            scenario_key="mumbai_offshore"
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertGreater(result["total_vessels_evaluated"], 0)
        
        vessels = result["suspect_vessels"]
        top_vessel = vessels[0]
        
        # Verify top vessel is MV OCEAN PRINCE with high suspicion score (~89%)
        self.assertEqual(top_vessel["name"], "MV OCEAN PRINCE")
        self.assertGreaterEqual(top_vessel["suspect_score"], 80.0)
        self.assertIn("distance", top_vessel["sub_scores"])
        self.assertIn("trajectory_similarity", top_vessel["sub_scores"])
        self.assertEqual(len(top_vessel["sub_scores"]), 7)

    def test_custom_weight_tuning(self):
        custom_w = {
            "distance": 0.50,
            "time_correlation": 0.50,
            "speed_change": 0.0,
            "course_change": 0.0,
            "ais_gap": 0.0,
            "loitering": 0.0,
            "trajectory_similarity": 0.0
        }

        result = self.engine.score_suspects(
            origin_lat=18.8780,
            origin_lon=72.3780,
            origin_time_str="2026-08-29T06:30:00Z",
            buffer_km=5.0,
            scenario_key="mumbai_offshore",
            custom_weights=custom_w
        )

        self.assertEqual(result["weights_used"]["distance"], 0.50)
        self.assertEqual(result["weights_used"]["speed_change"], 0.0)

if __name__ == "__main__":
    unittest.main()
