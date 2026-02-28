# core/predictions.py

import math
from .calculations import seconds_to_hms


def riegel_predict(t_seconds: float, d1_km: float, d2_km: float, exponent: float = 1.06) -> float:
    """Riegel formula: T2 = T1 * (D2/D1)^1.06"""
    if d1_km <= 0 or t_seconds <= 0:
        return 0.0
    return t_seconds * ((d2_km / d1_km) ** exponent)


def format_time_hms(total_seconds: float) -> str:
    h, m, s = seconds_to_hms(total_seconds)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def vo2max_from_race(distance_km: float, time_seconds: float) -> float:
    """
    Jack Daniels VDOT-based VO2max estimate.
    Uses the percentage of VO2max sustained at race pace formula.
    More accurate than Cooper for non-12-min efforts.
    """
    if time_seconds <= 0 or distance_km <= 0:
        return 0.0
    t_min = time_seconds / 60.0
    # Velocity in m/min
    velocity = (distance_km * 1000) / t_min
    # %VO2max sustained (Daniels & Gilbert)
    pct_vo2max = 0.8 + 0.1894393 * math.exp(-0.012778 * t_min) + 0.2989558 * math.exp(-0.1932605 * t_min)
    # VO2 at race pace
    vo2 = -4.60 + 0.182258 * velocity + 0.000104 * velocity ** 2
    return vo2 / pct_vo2max


def vdot_from_race(distance_km: float, time_seconds: float) -> float:
    """VDOT is effectively the same as VO2max from Daniels formula."""
    return vo2max_from_race(distance_km, time_seconds)


def training_paces(vdot: float) -> dict:
    """
    Returns Jack Daniels training pace ranges (seconds per km) from VDOT.
    Based on published VDOT tables / formulas.
    """
    if vdot <= 0:
        return {}

    # Find the velocity at VO2max (vVO2max) in m/min
    # Solve: vdot = -4.60 + 0.182258*v + 0.000104*v^2
    # Quadratic: 0.000104v^2 + 0.182258v - (vdot + 4.60) = 0
    a, b, c = 0.000104, 0.182258, -(vdot + 4.60)
    disc = b**2 - 4*a*c
    if disc < 0:
        return {}
    v_vo2max = (-b + math.sqrt(disc)) / (2 * a)  # m/min

    def pace_from_velocity(v_mpm):
        """Convert m/min velocity to seconds per km."""
        if v_mpm <= 0:
            return 0
        return (1000 / v_mpm) * 1  # seconds per km

    # Pace zones as % of vVO2max (Jack Daniels)
    zones = {
        "Easy":      (pace_from_velocity(v_vo2max * 0.59), pace_from_velocity(v_vo2max * 0.74)),
        "Marathon":  (pace_from_velocity(v_vo2max * 0.75), pace_from_velocity(v_vo2max * 0.84)),
        "Threshold": (pace_from_velocity(v_vo2max * 0.83), pace_from_velocity(v_vo2max * 0.88)),
        "Interval":  (pace_from_velocity(v_vo2max * 0.95), pace_from_velocity(v_vo2max * 1.00)),
        "Repetition":(pace_from_velocity(v_vo2max * 1.05), pace_from_velocity(v_vo2max * 1.15)),
    }
    return zones
