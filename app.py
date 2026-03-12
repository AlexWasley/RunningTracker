# gui/app.py

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.calculations import (
    Pace,
    get_time_seconds,
    seconds_to_hms,
    km_to_miles,
    average_speed,
)
from core.predictions import riegel_predict, format_time_hms, cooper_vo2max, simple_vdot_from_pace
from core.zones import zone_paces, seconds_to_min_sec
from core.utils import save_results_to_file


PRESET_DISTANCES_KM = {
    "5K": 5.0,
    "10K": 10.0,
    "Half Marathon": 21.097,
    "Marathon": 42.195,
    "Custom": None,
}


class RunningApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Running Pace & Race Performance Calculator")
        self.geometry("700x600")

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Unit selection
        ttk.Label(frame, text="Pace unit:").grid(row=0, column=0, sticky="w")
        self.unit_var = tk.StringVar(value="km")
        unit_combo = ttk.Combobox(frame, textvariable=self.unit_var, values=["km", "mile"], state="readonly")
        unit_combo.grid(row=0, column=1, sticky="w")

        # Pace inputs
        ttk.Label(frame, text="Pace minutes:").grid(row=1, column=0, sticky="w")
        self.pace_min_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.pace_min_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Pace seconds:").grid(row=2, column=0, sticky="w")
        self.pace_sec_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.pace_sec_var, width=10).grid(row=2, column=1, sticky="w")

        # Distance
        ttk.Label(frame, text="Distance preset:").grid(row=3, column=0, sticky="w")
        self.dist_preset_var = tk.StringVar(value="5K")
        dist_combo = ttk.Combobox(frame, textvariable=self.dist_preset_var,
                                  values=list(PRESET_DISTANCES_KM.keys()), state="readonly")
        dist_combo.grid(row=3, column=1, sticky="w")

        ttk.Label(frame, text="Custom distance (km):").grid(row=4, column=0, sticky="w")
        self.custom_dist_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.custom_dist_var, width=10).grid(row=4, column=1, sticky="w")

        # Buttons
        ttk.Button(frame, text="Calculate", command=self.calculate).grid(row=5, column=0, pady=10, sticky="w")
        ttk.Button(frame, text="Save Results", command=self.save_results).grid(row=5, column=1, pady=10, sticky="w")

        # Output
        self.output_text = tk.Text(frame, height=20, width=80)
        self.output_text.grid(row=6, column=0, columnspan=3, pady=10)

    def _parse_float(self, value: str, name: str):
        try:
            v = float(value)
            if v < 0:
                raise ValueError
            return v
        except ValueError:
            messagebox.showerror("Input error", f"Invalid {name}.")
            return None

    def _get_distance_km(self):
        preset = self.dist_preset_var.get()
        dist = PRESET_DISTANCES_KM.get(preset)
        if dist is None:
            v = self._parse_float(self.custom_dist_var.get(), "custom distance")
            return v
        return dist

    def calculate(self):
        unit = self.unit_var.get()
        pace_min = self._parse_float(self.pace_min_var.get(), "pace minutes")
        if pace_min is None:
            return
        pace_sec = self._parse_float(self.pace_sec_var.get(), "pace seconds")
        if pace_sec is None:
            return
        dist_km = self._get_distance_km()
        if dist_km is None:
            return

        pace = Pace(minutes=pace_min, seconds=pace_sec, unit=unit)

        if unit == "km":
            effective_distance = dist_km
        else:
            effective_distance = km_to_miles(dist_km)

        total_time_seconds = get_time_seconds(
            effective_distance, pace.total_seconds
        )
        h, m, s = seconds_to_hms(total_time_seconds)

        speed_kmh, speed_mph = average_speed(dist_km, total_time_seconds)

        distance_m = dist_km * 1000
        vo2 = cooper_vo2max(distance_m, total_time_seconds)
        vdot = simple_vdot_from_pace(pace.total_seconds)

        targets_km = [
            ("5K", 5.0),
            ("10K", 10.0),
            ("Half Marathon", 21.097),
            ("Marathon", 42.195),
        ]
        predictions = []
        for name, d_km in targets_km:
            t2 = riegel_predict(total_time_seconds, dist_km, d_km)
            predictions.append((name, d_km, t2))

        zones = zone_paces(pace.total_seconds)

        lines = []
        lines.append("=== Results ===")
        lines.append(f"Pace: {int(pace_min)}:{int(pace_sec):02d} per {unit}")
        lines.append(f"Distance: {dist_km:.3f} km ({km_to_miles(dist_km):.3f} miles)")
        lines.append(f"Predicted Time: {h}h {m}m {s}s")
        lines.append(f"Average speed: {speed_kmh:.2f} km/h ({speed_mph:.2f} mph)")
        lines.append(f"Estimated VO2max: {vo2:.1f}")
        lines.append(f"VDOT-like index: {vdot:.1f}")
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
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, output)
        self.last_output = output

    def save_results(self):
        output = getattr(self, "last_output", "").strip()
        if not output:
            messagebox.showwarning("No results", "Please calculate first.")
            return
        save_results_to_file(output)
        messagebox.showinfo("Saved", "Results saved to results.txt")


if __name__ == "__main__":
    app = RunningApp()
    app.mainloop()