"""Compare lift metrics across several exoskeleton assist ratios."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exosim.scenario import ScenarioConfig, simulate_lift


def main() -> None:
    output_path = ROOT / "outputs" / "assist_sweep_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for assist_ratio in (0.0, 0.2, 0.4, 0.6, 0.8):
        _, metrics = simulate_lift(ScenarioConfig(payload_kg=5.0, assist_ratio=assist_ratio))
        rows.append(metrics)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {output_path}")
    print("assist  peak human shoulder  peak human elbow  peak motor shoulder  peak motor elbow")
    for row in rows:
        print(
            "{assist_ratio:>5.0%} {peak_human_shoulder_nm:>20.2f} {peak_human_elbow_nm:>17.2f} {peak_motor_shoulder_nm:>20.2f} {peak_motor_elbow_nm:>17.2f}".format(
                **row
            )
        )


if __name__ == "__main__":
    main()
