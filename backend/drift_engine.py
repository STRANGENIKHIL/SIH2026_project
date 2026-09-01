"""
MetOcean Drift Simulation Engine: Lagrangian Particle Tracker
Calculates Backward Drift (Hindcasting) to locate spill origin (t0, x0, y0)
and Forward Drift (Forecasting) for spill containment modeling.
"""

import math
from datetime import datetime, timedelta

class DriftSimulator:
    def __init__(self):
        # MetOcean Vectors (Arabian Sea Monsoon/Post-monsoon pattern)
        self.u_current = 0.22  # m/s (Eastward)
        self.v_current = 0.14  # m/s (Northward)
        self.u_wind = 3.2      # m/s (10m surface wind)
        self.v_wind = 1.0      # m/s
        self.wind_leeway_factor = 0.035
        self.coriolis_angle_rad = math.radians(12.0)

    def _compute_total_velocity(self):
        """Calculates combined current + wind-leeway drift velocity (m/s)"""
        u_w_rot = self.u_wind * math.cos(self.coriolis_angle_rad) - self.v_wind * math.sin(self.coriolis_angle_rad)
        v_w_rot = self.u_wind * math.sin(self.coriolis_angle_rad) + self.v_wind * math.cos(self.coriolis_angle_rad)
        v_x_total = self.u_current + (self.wind_leeway_factor * u_w_rot)
        v_y_total = self.v_current + (self.wind_leeway_factor * v_w_rot)
        return v_x_total, v_y_total
