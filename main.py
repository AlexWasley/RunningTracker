# cli/main.py

import sys
from pathlib import Path

# Adjust import path if running directly
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.calculations import (
    Pace,
    get_time_seconds,
    seconds_to_hms,
    km_to_miles,
    miles_to_km,
    average_speed,
)
from core.predictions import riegel_predict, format_time_hms, cooper_vo2max, simple_vdot_from_pace
from core.zones import zone_paces, seconds_to_min_sec
from core.utils import save_results_to_file


PRESET_DISTANCES_KM = {
    "1": ("Custom", None),
    "2": ("5K", 5.0),
    "3": ("10K", 10.0),
    "4": ("Half Marathon", 21.097),
    "5": ("Marathon", 42.195),
}


def get_positive_float(prompt: str) -> float:
    while True:
        try:
            v = float(input(prompt))
            if v < 0:
                print("Value must be non-negative.")
            else:
                return v
        except ValueError:
            print("Invalid number, try again.")


def choose_unit() -> str:
    print("\nSelect pace unit:")
    print("1. Minutes per km")
    print("2. Minutes per mile")
    while True:
        c = input("Choose (1-2): ").strip()
        if c == "1":
            return "km"
        if c == "2":
            return "mile"
        print("Invalid choice.")


def choose_distance_km() -> float:
    print("\nChoose distance:")
    for key, (name, dist) in PRESET_DISTANCES_KM.items():
        if dist is None:
            print(f"{key}. {name} distance (enter manually)")
        else:
            print(f"{key}. {name} ({dist:.3f} km)")
    while True:
        choice = input("Select option: ").strip()
        if choice in PRESET_DISTANCES_KM:
            name, dist = PRESET_DISTANCES_KM[choice]
            if dist is not None:
                return dist
            return get_positive_float("Enter custom distance in km: ")
        print("Invalid choice.")


def main():
    print("Running Pace & Race Performance Calculator (CLI)")
    unit = choose_unit()
    pace_min = get_positive_float(f"Enter pace minutes per {unit}: ")
    pace_sec = get_positive_float(f"Enter pace seconds per {unit}: ")
    pace = Pace(minutes=pace_min, seconds=pace_sec, unit=unit)

    distance_km = choose_distance_km()
    if unit == "km":
        distance_display = distance_km
    else:
        distance_display = km_to_miles(distance_km)

    # Convert distance for calculations
    if unit == "km":
        effective_distance = distance_km
    else:
        effective_distance = km_to_miles(distance_km)

    total_time_seconds = get_time_seconds(
        distance_display if unit == "mile" else distance_km,
        pace.total_seconds,
    )

    h, m, s = seconds_to_hms(total_time_seconds)
    speed_kmh, speed_mph = average_speed(distance_km, total_time_seconds)

    # VO2max and predictions
    distance_m = distance_km * 1000
    vo2 = cooper_vo2max(distance_m, total_time_seconds)
    vdot = simple_vdot_from_pace(pace.total_seconds / (distance_display / distance_km if unit == "mile" else 1))

    # Race predictions via Riegel from this distance
    targets_km = [
        ("5K", 5.0),
        ("10K", 10.0),
        ("Half Marathon", 21.097),
        ("Marathon", 42.195),
    ]
    predictions = []
    for name, d_km in targets_km:
        t2 = riegel_predict(total_time_seconds, distance_km, d_km)
        predictions.append((name, d_km, t2))

    # Zones
    zones = zone_paces(pace.total_seconds)

    # Build output text
    lines = []
    lines.append("=== Results ===")
    lines.append(f"Pace: {int(pace_min)}:{int(pace_sec):02d} per {unit}")
    lines.append(f"Distance: {distance_km:.3f} km ({km_to_miles(distance_km):.3f} miles)")
    lines.append(f"Predicted Time: {h}h {m}m {s}s")
    lines.append(f"Average speed: {speed_kmh:.2f} km/h ({speed_mph:.2f} mph)")
    lines.append(f"Estimated VO2max (Cooper-style): {vo2:.1f}")
    lines.append(f"Simple VDOT-style index: {vdot:.1f}")
    lines.append("")
    lines.append("Race time predictions (Riegel):")
    for name, d_km, t2 in predictions:
        lines.append(f"  {name} ({d_km:.3f} km): {format_time_hms(t2)}")
    lines.append("")
    lines.append("Pace zones:")
    for z, lower, upper in zones:
        lm, ls = seconds_to_min_sec(lower)
        um, us = seconds_to_min_sec(upper)
        lines.append(
            f"  {z.name} [{z.color}]: {lm}:{ls:02d} - {um}:{us:02d} per km (approx)"
        )

    output = "\n".join(lines)
    print()
    print(output)

    # Save option
    ans = input("\nSave results to file? (y/n): ").strip().lower()
    if ans == "y":
        save_results_to_file(output)
        print("Results saved to results.txt")


if __name__ == "__main__":
    main()