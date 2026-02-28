# core/zones.py

from dataclasses import dataclass


@dataclass
class Zone:
    name: str
    lower_factor: float
    upper_factor: float
    color: str
    hr_pct_low: float   # % of max HR
    hr_pct_high: float
    description: str


ZONES = [
    Zone("Easy / Recovery", 1.20, 1.40, "#4ade80", 0.60, 0.70, "Builds aerobic base, aids recovery"),
    Zone("Steady / Aerobic", 1.10, 1.20, "#60a5fa", 0.70, 0.80, "Improves aerobic efficiency"),
    Zone("Tempo / Lactate", 0.95, 1.05, "#facc15", 0.80, 0.87, "Raises lactate threshold"),
    Zone("Threshold",        0.90, 0.95, "#fb923c", 0.87, 0.92, "Improves ability to sustain hard effort"),
    Zone("Interval / VO2",   0.80, 0.90, "#f87171", 0.92, 0.97, "Maximises VO2max and speed"),
]


def zone_paces(base_pace_seconds_per_km: float):
    results = []
    for z in ZONES:
        lower = base_pace_seconds_per_km * z.lower_factor
        upper = base_pace_seconds_per_km * z.upper_factor
        results.append((z, lower, upper))
    return results


def heart_rate_zones(max_hr: int):
    """Returns HR zones based on max HR."""
    results = []
    for z in ZONES:
        results.append({
            "name": z.name,
            "color": z.color,
            "hr_low": int(max_hr * z.hr_pct_low),
            "hr_high": int(max_hr * z.hr_pct_high),
            "description": z.description,
        })
    return results


def seconds_to_min_sec(sec: float):
    sec = int(round(sec))
    m = sec // 60
    s = sec % 60
    return m, s
