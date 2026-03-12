# core/predictions.py

from .calculations import seconds_to_hms

def riegel_predict(t_seconds: float, d1: float, d2: float, exponent: float = 1.06) -> float:
    # Riegel formula: T2 = T1 * (D2 / D1)^1.06
    if d1 <= 0:
        return 0.0
    ratio = d2 / d1
    return t_seconds * (ratio ** exponent)


def format_time_hms(total_seconds: float) -> str:
    h, m, s = seconds_to_hms(total_seconds)
    return f"{h}h {m}m {s}s"


def cooper_vo2max(distance_m: float, time_seconds: float) -> float:
    # Simple Cooper-style estimate: VO2max ≈ (distance_m - 504.9) / 44.73
    # This assumes 12-minute test; here we adjust very roughly by scaling.
    if time_seconds <= 0:
        return 0.0
    # Normalize to 12 minutes
    normalized_distance = distance_m * (12 * 60 / time_seconds)
    return (normalized_distance - 504.9) / 44.73


def simple_vdot_from_pace(pace_seconds_per_km: float) -> float:
    # Very rough VDOT-like metric: faster pace => higher value
    if pace_seconds_per_km <= 0:
        return 0.0
    # Example: 4:00/km ~ VDOT 60, 5:00/km ~ VDOT 50 etc. This is a crude approximation.
    minutes = pace_seconds_per_km / 60.0
    return max(20.0, 90.0 - (minutes * 10.0))