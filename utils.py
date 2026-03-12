# core/utils.py

from datetime import datetime

RESULTS_FILE = "results.txt"


def save_results_to_file(text: str, filepath: str = RESULTS_FILE, append: bool = True):
    mode = "a" if append else "w"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filepath, mode, encoding="utf-8") as f:
        f.write(f"[{timestamp}]\n{text}\n\n")