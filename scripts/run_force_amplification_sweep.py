"""Compare human load for simple force-amplification gains."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exosim.scenario import ScenarioConfig, simulate_lift


def main() -> None:
    output_path = ROOT / "outputs" / "force_amp_sweep_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for gain in (0.0, 0.5, 1.0, 1.5, 2.0):
        _, metrics = simulate_lift(
            ScenarioConfig(
                payload_kg=5.0,
                control_mode="force_amp",
                amplification_gain=gain,
                motor_response_time_s=0.0,
            )
        )
        rows.append(metrics)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {output_path}")
    print("gain  felt kg shoulder  felt kg elbow  peak human shoulder  peak motor shoulder")
    for row in rows:
        print(
            "{amplification_gain:>4.1f} {felt_payload_kg_by_shoulder_peak:>17.2f} {felt_payload_kg_by_elbow_peak:>14.2f} {peak_human_shoulder_nm:>20.2f} {peak_motor_shoulder_nm:>20.2f}".format(
                **row
            )
        )


if __name__ == "__main__":
    main()
