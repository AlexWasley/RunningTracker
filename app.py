# web/app.py

import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.calculations import (
    Pace, get_time_seconds, seconds_to_hms,
    km_to_miles, average_speed, get_km_splits, PRESET_DISTANCES_KM,
)
from core.predictions import (
    riegel_predict, format_time_hms,
    vo2max_from_race, vdot_from_race, training_paces,
)
from core.zones import zone_paces, heart_rate_zones, seconds_to_min_sec
from core.utils import save_results_to_file, fmt_pace

app = Flask(__name__, template_folder="templates", static_folder="static")


def build_context(unit, pace_min, pace_sec, dist_km, max_hr=None):
    """Core calculation logic, reused by both GET and POST."""
    errors = []
    if dist_km <= 0:
        errors.append("Distance must be greater than 0.")
    if pace_min == 0 and pace_sec == 0:
        errors.append("Pace cannot be zero.")
    if errors:
        return {"errors": errors}

    pace = Pace(minutes=pace_min, seconds=pace_sec, unit=unit)
    pace_per_km = pace.total_seconds_per_km  # always in sec/km

    total_time_seconds = get_time_seconds(dist_km, pace_per_km)
    h, m, s = seconds_to_hms(total_time_seconds)
    speed_kmh, speed_mph = average_speed(dist_km, total_time_seconds)

    # Accurate VO2max & VDOT using Jack Daniels formula
    vo2 = vo2max_from_race(dist_km, total_time_seconds)
    vdot = vdot_from_race(dist_km, total_time_seconds)

    # Race predictions
    targets = [("5K", 5.0), ("10K", 10.0), ("Half Marathon", 21.097), ("Marathon", 42.195)]
    predictions = []
    for name, d_km in targets:
        t2 = riegel_predict(total_time_seconds, dist_km, d_km)
        pace_pred = t2 / d_km
        predictions.append({
            "name": name,
            "distance_km": d_km,
            "time": format_time_hms(t2),
            "pace": fmt_pace(pace_pred),
        })

    # Pace zones
    zones = []
    for z, lower, upper in zone_paces(pace_per_km):
        zones.append({
            "name": z.name,
            "color": z.color,
            "lower": fmt_pace(lower),
            "upper": fmt_pace(upper),
            "description": z.description,
            "lower_sec": lower,
            "upper_sec": upper,
        })

    # Training paces from VDOT
    tp = training_paces(vdot)
    train_paces = []
    for name, (slow, fast) in tp.items():
        train_paces.append({
            "name": name,
            "slow": fmt_pace(slow),
            "fast": fmt_pace(fast),
            "slow_sec": slow,
            "fast_sec": fast,
        })

    # Per-km splits
    splits = get_km_splits(dist_km, pace_per_km)

    # Heart rate zones
    hr_zones = []
    if max_hr and max_hr > 0:
        hr_zones = heart_rate_zones(int(max_hr))

    # Pace per mile display
    pace_per_mile = pace.total_seconds if unit == "mile" else pace_per_km * 1.609344

    return {
        "errors": [],
        "unit": unit,
        "pace_min": int(pace_min),
        "pace_sec": int(pace_sec),
        "pace_per_km": fmt_pace(pace_per_km),
        "pace_per_mile": fmt_pace(pace_per_mile),
        "distance_km": dist_km,
        "distance_miles": km_to_miles(dist_km),
        "time_h": h, "time_m": m, "time_s": s,
        "total_seconds": total_time_seconds,
        "speed_kmh": round(speed_kmh, 2),
        "speed_mph": round(speed_mph, 2),
        "vo2": round(vo2, 1),
        "vdot": round(vdot, 1),
        "predictions": predictions,
        "zones": zones,
        "train_paces": train_paces,
        "splits": splits,
        "hr_zones": hr_zones,
        "max_hr": max_hr,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            unit = request.form.get("unit", "km")
            pace_min = float(request.form.get("pace_min", 0) or 0)
            pace_sec = float(request.form.get("pace_sec", 0) or 0)
            preset = request.form.get("distance_preset", "5K")
            custom_dist = request.form.get("custom_distance", "") or 0
            max_hr = request.form.get("max_hr", "") or None
            if max_hr:
                max_hr = int(max_hr)

            dist_km = PRESET_DISTANCES_KM.get(preset)
            if dist_km is None:
                dist_km = float(custom_dist)

            context = build_context(unit, pace_min, pace_sec, dist_km, max_hr)

            if not context["errors"] and "save" in request.form:
                lines = [
                    f"Pace: {context['pace_per_km']}/km  ({context['pace_per_mile']}/mile)",
                    f"Distance: {dist_km:.3f} km ({context['distance_miles']:.3f} miles)",
                    f"Predicted Time: {context['time_h']}h {context['time_m']}m {context['time_s']}s",
                    f"Speed: {context['speed_kmh']} km/h ({context['speed_mph']} mph)",
                    f"VO2max: {context['vo2']}  VDOT: {context['vdot']}",
                    "", "Race Predictions:",
                ]
                for p in context["predictions"]:
                    lines.append(f"  {p['name']}: {p['time']}  ({p['pace']}/km)")
                save_results_to_file("\n".join(lines))
                context["saved"] = True

            return render_template("results.html", presets=PRESET_DISTANCES_KM.keys(), **context)

        except (ValueError, TypeError) as e:
            return render_template("index.html", presets=PRESET_DISTANCES_KM.keys(),
                                   error=f"Invalid input: {e}")

    return render_template("index.html", presets=PRESET_DISTANCES_KM.keys())


if __name__ == "__main__":
    app.run(debug=True)
