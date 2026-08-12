"""Compare force amplification with good and bad torque-sensor assumptions."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exosim.scenario import ScenarioConfig, simulate_lift


def main() -> None:
    output_path = ROOT / "outputs" / "sensor_feedback_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for sensor_mode in ("human_only", "combined"):
        for response_time_s in (0.0, 0.03, 0.08):
            _, metrics = simulate_lift(
                ScenarioConfig(
                    payload_kg=5.0,
                    control_mode="force_amp",
                    force_sensor_mode=sensor_mode,
                    amplification_gain=1.0,
                    motor_response_time_s=response_time_s,
                )
            )
            rows.append(metrics)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {output_path}")
    print("sensor      lag_ms  felt_shoulder  peak_motor_shoulder  max_shoulder_error")
    for row in rows:
        lag_ms = round(float(row.get("motor_response_time_s", 0.0)) * 1000.0)
        print(
            "{force_sensor_mode:<10} {lag_ms:>6} {felt_payload_kg_by_shoulder_peak:>14.2f} {peak_motor_shoulder_nm:>21.2f} {shoulder_tracking_max_abs_deg:>19.2f}".format(
                lag_ms=lag_ms,
                **row,
            )
        )


if __name__ == "__main__":
    main()
