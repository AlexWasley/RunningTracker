# core/calculations.py

from dataclasses import dataclass

KM_PER_MILE = 1.609344
MILE_PER_KM = 1 / KM_PER_MILE

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
            return self.total_seconds / KM_PER_MILE
        return self.total_seconds


def get_time_seconds(distance: float, pace_seconds: float) -> float:
    return distance * pace_seconds


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