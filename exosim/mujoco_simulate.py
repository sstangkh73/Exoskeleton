"""MuJoCo-backed 3D arm simulation runner."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import time
from typing import Dict, Iterable, Tuple
import xml.etree.ElementTree as ET

from .scenario import ScenarioConfig, target_at

Pair = Tuple[float, float]
LogRow = Dict[str, float]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "models" / "arm_exoskeleton_3d.xml"


def import_mujoco():
    try:
        import mujoco
    except ImportError as exc:
        raise SystemExit(
            "MuJoCo is not installed for this Python. Install it with:\n"
            "  python -m pip install -r requirements.txt\n"
            "or:\n"
            "  python -m pip install mujoco\n"
        ) from exc
    return mujoco


def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def write_csv(path: str | Path, rows: Iterable[LogRow]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError("cannot write empty log")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def set_joint_state(data, joint_name: str, qpos: float, qvel: float = 0.0) -> None:
    joint = data.joint(joint_name)
    joint.qpos[0] = qpos
    joint.qvel[0] = qvel


def dof_index(model, joint_name: str) -> int:
    return int(model.joint(joint_name).dofadr[0])


def actuator_index(model, actuator_name: str) -> int:
    return int(model.actuator(actuator_name).id)


def load_model(mujoco, model_path: Path, payload_kg: float):
    tree = ET.parse(model_path)
    root = tree.getroot()
    for geom in root.iter("geom"):
        if geom.attrib.get("name") == "payload_geom":
            geom.set("mass", f"{payload_kg:.9g}")
            xml_text = ET.tostring(root, encoding="unicode")
            return mujoco.MjModel.from_xml_string(xml_text)
    raise ValueError("payload_geom not found in MuJoCo model")


def body_pos(data, body_name: str) -> Tuple[float, float, float]:
    pos = data.body(body_name).xpos
    return float(pos[0]), float(pos[1]), float(pos[2])


def joint_position(data, joint_name: str) -> float:
    return float(data.joint(joint_name).qpos[0])


def joint_velocity(data, joint_name: str) -> float:
    return float(data.joint(joint_name).qvel[0])


def target_control_torque(
    *,
    bias_torque: Pair,
    current_q: Pair,
    current_dq: Pair,
    target_q: Pair,
    target_dq: Pair,
) -> Pair:
    shoulder_kp = 90.0
    elbow_kp = 60.0
    shoulder_kd = 14.0
    elbow_kd = 9.0
    shoulder = (
        bias_torque[0]
        + shoulder_kp * (target_q[0] - current_q[0])
        + shoulder_kd * (target_dq[0] - current_dq[0])
    )
    elbow = (
        bias_torque[1]
        + elbow_kp * (target_q[1] - current_q[1])
        + elbow_kd * (target_dq[1] - current_dq[1])
    )
    return shoulder, elbow


def summarize(
    logs: list[LogRow],
    payload_kg: float,
    control_mode: str,
    force_sensor_mode: str,
    amplification_gain: float,
    motor_response_time_s: float,
) -> Dict[str, float | str]:
    def peak_abs(field: str) -> float:
        return max(abs(row[field]) for row in logs)

    peak_total_shoulder = peak_abs("total_shoulder_nm")
    peak_total_elbow = peak_abs("total_elbow_nm")
    shoulder_fraction = peak_abs("human_shoulder_nm") / max(peak_total_shoulder, 1e-9)
    elbow_fraction = peak_abs("human_elbow_nm") / max(peak_total_elbow, 1e-9)
    shoulder_error_rms = math.sqrt(
        sum(row["shoulder_error_deg"] ** 2 for row in logs) / len(logs)
    )
    elbow_error_rms = math.sqrt(sum(row["elbow_error_deg"] ** 2 for row in logs) / len(logs))
    shoulder_saturation_fraction = sum(
        1.0 for row in logs if abs(row["motor_shoulder_nm"]) >= 80.0 - 1e-6
    ) / len(logs)
    elbow_saturation_fraction = sum(
        1.0 for row in logs if abs(row["motor_elbow_nm"]) >= 60.0 - 1e-6
    ) / len(logs)
    return {
        "payload_kg": payload_kg,
        "control_mode": control_mode,
        "force_sensor_mode": force_sensor_mode,
        "amplification_gain": amplification_gain,
        "motor_response_time_s": motor_response_time_s,
        "duration_s": logs[-1]["time_s"],
        "peak_human_shoulder_nm": peak_abs("human_shoulder_nm"),
        "peak_human_elbow_nm": peak_abs("human_elbow_nm"),
        "peak_motor_shoulder_nm": peak_abs("motor_shoulder_nm"),
        "peak_motor_elbow_nm": peak_abs("motor_elbow_nm"),
        "shoulder_motor_saturation_fraction": shoulder_saturation_fraction,
        "elbow_motor_saturation_fraction": elbow_saturation_fraction,
        "peak_measured_shoulder_nm": peak_abs("measured_shoulder_nm"),
        "peak_measured_elbow_nm": peak_abs("measured_elbow_nm"),
        "peak_total_shoulder_nm": peak_total_shoulder,
        "peak_total_elbow_nm": peak_total_elbow,
        "felt_payload_kg_by_shoulder_peak": payload_kg * shoulder_fraction,
        "felt_payload_kg_by_elbow_peak": payload_kg * elbow_fraction,
        "shoulder_tracking_rms_deg": shoulder_error_rms,
        "elbow_tracking_rms_deg": elbow_error_rms,
        "shoulder_tracking_max_abs_deg": peak_abs("shoulder_error_deg"),
        "elbow_tracking_max_abs_deg": peak_abs("elbow_error_deg"),
        "start_hand_z_m": logs[0]["hand_z_m"],
        "end_hand_z_m": logs[-1]["hand_z_m"],
        "lift_height_m": logs[-1]["hand_z_m"] - logs[0]["hand_z_m"],
    }


def simulate_3d(config: ScenarioConfig, model_path: Path, viewer: bool = False):
    mujoco = import_mujoco()
    model = load_model(mujoco, model_path, config.payload_kg)
    data = mujoco.MjData(model)
    model.opt.timestep = config.dt_s

    shoulder_dof = dof_index(model, "shoulder_flexion")
    elbow_dof = dof_index(model, "elbow_flexion")
    shoulder_actuator = actuator_index(model, "shoulder_motor")
    elbow_actuator = actuator_index(model, "elbow_motor")

    start_q, _ = target_at(config, 0.0)
    set_joint_state(data, "shoulder_flexion", start_q[0])
    set_joint_state(data, "elbow_flexion", start_q[1])
    mujoco.mj_forward(model, data)

    logs: list[LogRow] = []
    steps = int(round(config.duration_s / config.dt_s))
    previous_motor_torque = (0.0, 0.0)

    viewer_handle = None
    if viewer:
        import mujoco.viewer

        viewer_handle = mujoco.viewer.launch_passive(model, data)

    try:
        for index in range(steps + 1):
            step_start = time.time()
            time_s = min(index * config.dt_s, config.duration_s)
            target_q, target_dq = target_at(config, time_s)
            mujoco.mj_forward(model, data)

            current_q = (
                joint_position(data, "shoulder_flexion"),
                joint_position(data, "elbow_flexion"),
            )
            current_dq = (
                joint_velocity(data, "shoulder_flexion"),
                joint_velocity(data, "elbow_flexion"),
            )
            shoulder_error = target_q[0] - current_q[0]
            elbow_error = target_q[1] - current_q[1]
            bias = (
                float(data.qfrc_bias[shoulder_dof]),
                float(data.qfrc_bias[elbow_dof]),
            )
            desired_total = target_control_torque(
                bias_torque=bias,
                current_q=current_q,
                current_dq=current_dq,
                target_q=target_q,
                target_dq=target_dq,
            )

            if config.control_mode == "gravity":
                motor_torque = (
                    config.assist_ratio * bias[0],
                    config.assist_ratio * bias[1],
                )
                measured_torque = (0.0, 0.0)
                human_torque = (
                    desired_total[0] - motor_torque[0],
                    desired_total[1] - motor_torque[1],
                )
            elif config.control_mode == "force_amp":
                gain = max(0.0, config.amplification_gain)
                human_torque = (
                    desired_total[0] / (1.0 + gain),
                    desired_total[1] / (1.0 + gain),
                )
                if config.force_sensor_mode == "human_only":
                    measured_torque = human_torque
                elif config.force_sensor_mode == "combined":
                    measured_torque = (
                        human_torque[0] + previous_motor_torque[0],
                        human_torque[1] + previous_motor_torque[1],
                    )
                else:
                    raise ValueError("force_sensor_mode must be 'human_only' or 'combined'")

                motor_target = (gain * measured_torque[0], gain * measured_torque[1])
                if config.motor_response_time_s <= 0.0:
                    motor_torque = motor_target
                else:
                    alpha = clamp(config.dt_s / config.motor_response_time_s, 0.0, 1.0)
                    motor_torque = (
                        previous_motor_torque[0]
                        + (motor_target[0] - previous_motor_torque[0]) * alpha,
                        previous_motor_torque[1]
                        + (motor_target[1] - previous_motor_torque[1]) * alpha,
                    )
            else:
                raise ValueError("control_mode must be 'gravity' or 'force_amp'")

            motor_torque = (
                clamp(motor_torque[0], -80.0, 80.0),
                clamp(motor_torque[1], -60.0, 60.0),
            )
            total_torque = (
                human_torque[0] + motor_torque[0],
                human_torque[1] + motor_torque[1],
            )

            data.qfrc_applied[:] = 0.0
            data.qfrc_applied[shoulder_dof] = human_torque[0]
            data.qfrc_applied[elbow_dof] = human_torque[1]
            data.ctrl[shoulder_actuator] = motor_torque[0]
            data.ctrl[elbow_actuator] = motor_torque[1]

            hand_x, hand_y, hand_z = body_pos(data, "payload")
            logs.append(
                {
                    "time_s": time_s,
                    "shoulder_deg": rad_to_deg(current_q[0]),
                    "elbow_deg": rad_to_deg(current_q[1]),
                    "target_shoulder_deg": rad_to_deg(target_q[0]),
                    "target_elbow_deg": rad_to_deg(target_q[1]),
                    "shoulder_error_deg": rad_to_deg(shoulder_error),
                    "elbow_error_deg": rad_to_deg(elbow_error),
                    "bias_shoulder_nm": bias[0],
                    "bias_elbow_nm": bias[1],
                    "human_shoulder_nm": human_torque[0],
                    "human_elbow_nm": human_torque[1],
                    "measured_shoulder_nm": measured_torque[0],
                    "measured_elbow_nm": measured_torque[1],
                    "motor_shoulder_nm": motor_torque[0],
                    "motor_elbow_nm": motor_torque[1],
                    "total_shoulder_nm": total_torque[0],
                    "total_elbow_nm": total_torque[1],
                    "hand_x_m": hand_x,
                    "hand_y_m": hand_y,
                    "hand_z_m": hand_z,
                }
            )

            if index < steps:
                mujoco.mj_step(model, data)
                previous_motor_torque = motor_torque

            if viewer_handle is not None:
                viewer_handle.sync()
                sleep_s = model.opt.timestep - (time.time() - step_start)
                if sleep_s > 0:
                    time.sleep(sleep_s)
    finally:
        if viewer_handle is not None:
            viewer_handle.close()

    return logs, summarize(
        logs,
        config.payload_kg,
        config.control_mode,
        config.force_sensor_mode,
        config.amplification_gain,
        config.motor_response_time_s,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the 3D MuJoCo arm simulation.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--payload-kg", type=float, default=5.0)
    parser.add_argument("--control-mode", choices=("gravity", "force_amp"), default="force_amp")
    parser.add_argument("--force-sensor-mode", choices=("human_only", "combined"), default="human_only")
    parser.add_argument("--assist", type=float, default=0.5)
    parser.add_argument("--amplification-gain", type=float, default=1.0)
    parser.add_argument("--felt-payload-kg", type=float)
    parser.add_argument("--motor-response-time-s", type=float, default=0.03)
    parser.add_argument("--duration-s", type=float, default=3.0)
    parser.add_argument("--dt", type=float, default=0.005)
    parser.add_argument("--start-shoulder-deg", type=float, default=15.0)
    parser.add_argument("--start-elbow-deg", type=float, default=75.0)
    parser.add_argument("--end-shoulder-deg", type=float, default=65.0)
    parser.add_argument("--end-elbow-deg", type=float, default=45.0)
    parser.add_argument("--output", default="outputs/lift_3d.csv")
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--json", action="store_true")
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
    logs, metrics = simulate_3d(config, args.model, viewer=args.viewer)
    write_csv(args.output, logs)

    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return

    print(f"wrote {len(logs)} samples to {args.output}")
    print(
        "3D mode={control_mode} sensor={force_sensor_mode} payload={payload_kg:.2f} kg lift={lift_height_m:.3f} m".format(
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
        "felt payload estimate: shoulder={felt_payload_kg_by_shoulder_peak:.2f} kg, elbow={felt_payload_kg_by_elbow_peak:.2f} kg".format(
            **metrics
        )
    )


if __name__ == "__main__":
    main()
