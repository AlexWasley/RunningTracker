# core/calculations.py

from dataclasses import dataclass

KM_PER_MILE = 1.609344
MILE_PER_KM = 1 / KM_PER_MILE

PRESET_DISTANCES_KM = {
    "5K": 5.0,
    "10K": 10.0,
    "Half Marathon": 21.097,
    "Marathon": 42.195,
    "Custom": None,
}

@dataclass
class Pace:
    minutes: float
    seconds: float
    unit: str  # "km" or "mile"

    @property
    def total_seconds(self) -> float:
        return self.minutes * 60 + self.seconds

    @property
    def total_seconds_per_km(self) -> float:
        """Always returns pace in seconds per km regardless of input unit."""
        if self.unit == "mile":
            return self.total_seconds * MILE_PER_KM
        return self.total_seconds


def get_time_seconds(distance_km: float, pace_seconds_per_km: float) -> float:
    """Calculate total time. Always use km-based inputs."""
    return distance_km * pace_seconds_per_km


def seconds_to_hms(total_seconds: float):
    total_seconds = int(round(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return hours, minutes, seconds


def km_to_miles(km: float) -> float:
    return km * MILE_PER_KM


def miles_to_km(miles: float) -> float:
    return miles * KM_PER_MILE


def average_speed(distance_km: float, total_seconds: float):
    hours = total_seconds / 3600.0
    if hours == 0:
        return 0.0, 0.0
    speed_kmh = distance_km / hours
    speed_mph = km_to_miles(distance_km) / hours
    return speed_kmh, speed_mph


def get_km_splits(distance_km: float, pace_seconds_per_km: float):
    """Return list of (split_label, elapsed_time_str) for each km."""
    splits = []
    full_km = int(distance_km)
    for i in range(1, full_km + 1):
        elapsed = i * pace_seconds_per_km
        h, m, s = seconds_to_hms(elapsed)
        splits.append({
            "label": f"km {i}",
            "split_time": _fmt_pace(pace_seconds_per_km),
            "elapsed": f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}",
        })
    # Partial last km
    remainder = distance_km - full_km
    if remainder > 0.01:
        elapsed = distance_km * pace_seconds_per_km
        h, m, s = seconds_to_hms(elapsed)
        partial_pace = remainder * pace_seconds_per_km
        splits.append({
            "label": f"km {distance_km:.1f}",
            "split_time": _fmt_pace(partial_pace),
            "elapsed": f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}",
        })
    return splits


def _fmt_pace(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"
