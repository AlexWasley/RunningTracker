# core/zones.py

from dataclasses import dataclass

@dataclass
class Zone:
    name: str
    lower_factor: float  # multiplier on base pace seconds
    upper_factor: float
    color: str  # text label; GUI/web can map to real colors


ZONES = [
    Zone("Easy", 1.15, 1.40, "green"),
    Zone("Steady", 1.05, 1.15, "blue"),
    Zone("Tempo", 0.95, 1.05, "yellow"),
    Zone("Threshold", 0.90, 0.95, "orange"),
    Zone("Interval", 0.80, 0.90, "red"),
]


def zone_paces(base_pace_seconds: float):
    results = []
    for z in ZONES:
        lower = base_pace_seconds * z.lower_factor
        upper = base_pace_seconds * z.upper_factor
        results.append((z, lower, upper))
    return results


def seconds_to_min_sec(sec: float):
    sec = int(round(sec))
    m = sec // 60
    s = sec % 60
    return m, s