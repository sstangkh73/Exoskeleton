"""Command-line entrypoint for the lift simulation."""

from __future__ import annotations

import argparse
import json

from .scenario import ScenarioConfig, simulate_lift, write_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a two-link arm lift simulation.")
    parser.add_argument("--payload-kg", type=float, default=5.0)
    parser.add_argument(
        "--control-mode",
        choices=("gravity", "force_amp"),
        default="gravity",
        help="gravity uses model-based gravity compensation; force_amp mirrors measured human torque.",
    )
    parser.add_argument(
        "--force-sensor-mode",
        choices=("human_only", "combined"),
        default="human_only",
        help="For force_amp: human_only reads user torque; combined reads user plus previous motor torque.",
    )
    parser.add_argument("--assist", type=float, default=0.4, help="Gravity assist ratio 0..1.")
    parser.add_argument(
        "--amplification-gain",
        type=float,
        default=1.0,
        help="For force_amp: motor torque = gain * measured human torque.",
    )
    parser.add_argument(
        "--felt-payload-kg",
        type=float,
        help="For force_amp: choose gain so payload feels like this mass, e.g. 5 -> 2.5 gives gain 1.",
    )
    parser.add_argument(
        "--motor-response-time-s",
        type=float,
        default=0.03,
        help="First-order motor response lag for force_amp.",
    )
    parser.add_argument("--duration-s", type=float, default=3.0)
    parser.add_argument("--dt", type=float, default=0.005)
    parser.add_argument("--start-shoulder-deg", type=float, default=15.0)
    parser.add_argument("--start-elbow-deg", type=float, default=75.0)
    parser.add_argument("--end-shoulder-deg", type=float, default=65.0)
    parser.add_argument("--end-elbow-deg", type=float, default=45.0)
    parser.add_argument("--output", default="outputs/lift.csv", help="CSV time-series output.")
    parser.add_argument("--json", action="store_true", help="Print metrics as JSON.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    amplification_gain = args.amplification_gain
    if args.felt_payload_kg is not None:
        if args.felt_payload_kg <= 0.0:
            raise SystemExit("--felt-payload-kg must be positive")
        amplification_gain = max(0.0, args.payload_kg / args.felt_payload_kg - 1.0)

    config = ScenarioConfig(
        payload_kg=args.payload_kg,
        control_mode=args.control_mode,
        force_sensor_mode=args.force_sensor_mode,
        assist_ratio=args.assist,
        amplification_gain=amplification_gain,
        motor_response_time_s=args.motor_response_time_s,
        duration_s=args.duration_s,
        dt_s=args.dt,
        start_shoulder_deg=args.start_shoulder_deg,
        start_elbow_deg=args.start_elbow_deg,
        end_shoulder_deg=args.end_shoulder_deg,
        end_elbow_deg=args.end_elbow_deg,
    )
    logs, metrics = simulate_lift(config)
    write_csv(args.output, logs)

    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return

    print(f"wrote {len(logs)} samples to {args.output}")
    print(
        "payload={payload_kg:.2f} kg mode={control_mode} sensor={force_sensor_mode} lift={lift_height_m:.3f} m".format(
            **metrics
        )
    )
    print(
        "peak human torque: shoulder={peak_human_shoulder_nm:.2f} Nm, elbow={peak_human_elbow_nm:.2f} Nm".format(
            **metrics
        )
    )
    print(
        "peak motor torque: shoulder={peak_motor_shoulder_nm:.2f} Nm, elbow={peak_motor_elbow_nm:.2f} Nm".format(
            **metrics
        )
    )
    print(
        "tracking RMS: shoulder={shoulder_tracking_rms_deg:.2f} deg, elbow={elbow_tracking_rms_deg:.2f} deg".format(
            **metrics
        )
    )
    print(
        "felt payload estimate: shoulder={felt_payload_kg_by_shoulder_peak:.2f} kg, elbow={felt_payload_kg_by_elbow_peak:.2f} kg".format(
            **metrics
        )
    )


if __name__ == "__main__":
    main()
