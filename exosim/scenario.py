"""Lift scenarios and metrics for the arm exoskeleton simulator."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .arm import ArmParameters, ArmState, Pair, TwoLinkArmModel, add_pair, subtract_pair
from .controllers import (
    ForceAmplificationController,
    GravityAssistController,
    HumanTrackingController,
)

LogRow = Dict[str, float]
MetricValue = float | str


@dataclass(frozen=True)
class ScenarioConfig:
    payload_kg: float = 5.0
    control_mode: str = "gravity"
    force_sensor_mode: str = "human_only"
    assist_ratio: float = 0.4
    amplification_gain: float = 1.0
    motor_response_time_s: float = 0.03
    duration_s: float = 3.0
    dt_s: float = 0.005
    start_shoulder_deg: float = 15.0
    start_elbow_deg: float = 75.0
    end_shoulder_deg: float = 65.0
    end_elbow_deg: float = 45.0


def deg_to_rad(deg: float) -> float:
    return math.radians(deg)


def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)


def smoothstep(alpha: float) -> Tuple[float, float]:
    """Return position and derivative scale for a cubic smoothstep."""

    alpha = max(0.0, min(1.0, alpha))
    position = 3.0 * alpha**2 - 2.0 * alpha**3
    derivative = 6.0 * alpha - 6.0 * alpha**2
    return position, derivative


def target_at(config: ScenarioConfig, time_s: float) -> Tuple[Pair, Pair]:
    duration = max(config.duration_s, 1e-9)
    alpha = time_s / duration
    blend, d_blend_d_alpha = smoothstep(alpha)
    d_blend_dt = d_blend_d_alpha / duration
    start = (
        deg_to_rad(config.start_shoulder_deg),
        deg_to_rad(config.start_elbow_deg),
    )
    end = (deg_to_rad(config.end_shoulder_deg), deg_to_rad(config.end_elbow_deg))
    delta = (end[0] - start[0], end[1] - start[1])
    q = (start[0] + delta[0] * blend, start[1] + delta[1] * blend)
    dq = (delta[0] * d_blend_dt, delta[1] * d_blend_dt)
    return q, dq


def simulate_lift(config: ScenarioConfig) -> Tuple[List[LogRow], Dict[str, MetricValue]]:
    """Run a scripted lift and return time-series logs plus summary metrics."""

    if config.dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    if config.duration_s <= 0.0:
        raise ValueError("duration_s must be positive")
    if config.payload_kg < 0.0:
        raise ValueError("payload_kg must be non-negative")
    if config.control_mode not in {"gravity", "force_amp"}:
        raise ValueError("control_mode must be 'gravity' or 'force_amp'")
    if config.force_sensor_mode not in {"human_only", "combined"}:
        raise ValueError("force_sensor_mode must be 'human_only' or 'combined'")

    params = ArmParameters(payload_mass_kg=config.payload_kg)
    model = TwoLinkArmModel(params)
    gravity_assist = GravityAssistController(config.assist_ratio)
    force_amp = ForceAmplificationController(
        gain=config.amplification_gain,
        response_time_s=config.motor_response_time_s,
    )
    human = HumanTrackingController()
    start_q, _ = target_at(config, 0.0)
    state = ArmState(start_q[0], start_q[1])
    logs: List[LogRow] = []
    steps = int(round(config.duration_s / config.dt_s))
    previous_motor_torque = (0.0, 0.0)

    motor_positive_work_j = 0.0
    human_positive_work_j = 0.0

    for index in range(steps + 1):
        time_s = min(index * config.dt_s, config.duration_s)
        target_q, target_dq = target_at(config, time_s)
        gravity = model.gravity_torque(state.q)

        if config.control_mode == "gravity":
            motor_torque = gravity_assist.motor_torque(model, state)
            measured_torque = (0.0, 0.0)
            remaining_gravity = subtract_pair(gravity, motor_torque)
            human_torque = human.torque(
                model,
                state,
                target_q=target_q,
                target_dq=target_dq,
                feedforward_torque=remaining_gravity,
            )
            human_effort_scale = 1.0
        else:
            gain = max(0.0, config.amplification_gain)
            human_effort_scale = 1.0 / (1.0 + gain)
            human_torque = human.torque(
                model,
                state,
                target_q=target_q,
                target_dq=target_dq,
                feedforward_torque=gravity,
                effort_scale=human_effort_scale,
            )
            if config.force_sensor_mode == "human_only":
                measured_torque = human_torque
            else:
                measured_torque = add_pair(human_torque, previous_motor_torque)
            motor_torque = force_amp.motor_torque(
                model=model,
                measured_human_torque=measured_torque,
                previous_motor_torque=previous_motor_torque,
                dt_s=config.dt_s,
            )

        total_torque = add_pair(human_torque, motor_torque)
        shoulder_acc, elbow_acc = model.acceleration(state, total_torque)
        elbow_x, elbow_y, hand_x, hand_y = model.forward_kinematics(state.q)
        error_shoulder = target_q[0] - state.shoulder_rad
        error_elbow = target_q[1] - state.elbow_rad

        logs.append(
            {
                "time_s": time_s,
                "shoulder_deg": rad_to_deg(state.shoulder_rad),
                "elbow_deg": rad_to_deg(state.elbow_rad),
                "shoulder_velocity_rad_s": state.shoulder_velocity_rad_s,
                "elbow_velocity_rad_s": state.elbow_velocity_rad_s,
                "shoulder_acc_rad_s2": shoulder_acc,
                "elbow_acc_rad_s2": elbow_acc,
                "target_shoulder_deg": rad_to_deg(target_q[0]),
                "target_elbow_deg": rad_to_deg(target_q[1]),
                "shoulder_error_deg": rad_to_deg(error_shoulder),
                "elbow_error_deg": rad_to_deg(error_elbow),
                "gravity_shoulder_nm": gravity[0],
                "gravity_elbow_nm": gravity[1],
                "motor_shoulder_nm": motor_torque[0],
                "motor_elbow_nm": motor_torque[1],
                "human_shoulder_nm": human_torque[0],
                "human_elbow_nm": human_torque[1],
                "measured_shoulder_nm": measured_torque[0],
                "measured_elbow_nm": measured_torque[1],
                "total_shoulder_nm": total_torque[0],
                "total_elbow_nm": total_torque[1],
                "human_effort_scale": human_effort_scale,
                "amplification_gain": config.amplification_gain,
                "elbow_x_m": elbow_x,
                "elbow_y_m": elbow_y,
                "hand_x_m": hand_x,
                "hand_y_m": hand_y,
            }
        )

        if index < steps:
            motor_power = (
                motor_torque[0] * state.shoulder_velocity_rad_s
                + motor_torque[1] * state.elbow_velocity_rad_s
            )
            human_power = (
                human_torque[0] * state.shoulder_velocity_rad_s
                + human_torque[1] * state.elbow_velocity_rad_s
            )
            motor_positive_work_j += max(0.0, motor_power) * config.dt_s
            human_positive_work_j += max(0.0, human_power) * config.dt_s
            state = model.step(state, total_torque, config.dt_s)
            previous_motor_torque = motor_torque

    metrics = summarize_logs(
        logs,
        payload_kg=config.payload_kg,
        control_mode=config.control_mode,
        force_sensor_mode=config.force_sensor_mode,
        assist_ratio=config.assist_ratio,
        amplification_gain=config.amplification_gain,
        motor_response_time_s=config.motor_response_time_s,
        motor_positive_work_j=motor_positive_work_j,
        human_positive_work_j=human_positive_work_j,
    )
    return logs, metrics


def summarize_logs(
    logs: List[LogRow],
    *,
    payload_kg: float,
    control_mode: str,
    force_sensor_mode: str,
    assist_ratio: float,
    amplification_gain: float,
    motor_response_time_s: float,
    motor_positive_work_j: float,
    human_positive_work_j: float,
) -> Dict[str, MetricValue]:
    if not logs:
        raise ValueError("logs cannot be empty")

    def peak_abs(field: str) -> float:
        return max(abs(row[field]) for row in logs)

    shoulder_error_rms = math.sqrt(
        sum(row["shoulder_error_deg"] ** 2 for row in logs) / len(logs)
    )
    elbow_error_rms = math.sqrt(sum(row["elbow_error_deg"] ** 2 for row in logs) / len(logs))
    shoulder_error_max = peak_abs("shoulder_error_deg")
    elbow_error_max = peak_abs("elbow_error_deg")
    start_hand_height = logs[0]["hand_y_m"]
    end_hand_height = logs[-1]["hand_y_m"]
    peak_human_shoulder = peak_abs("human_shoulder_nm")
    peak_human_elbow = peak_abs("human_elbow_nm")
    peak_total_shoulder = peak_abs("total_shoulder_nm")
    peak_total_elbow = peak_abs("total_elbow_nm")
    shoulder_human_fraction = peak_human_shoulder / max(peak_total_shoulder, 1e-9)
    elbow_human_fraction = peak_human_elbow / max(peak_total_elbow, 1e-9)
    shoulder_motor_limit = 80.0
    elbow_motor_limit = 60.0
    shoulder_saturation_fraction = sum(
        1.0 for row in logs if abs(row["motor_shoulder_nm"]) >= shoulder_motor_limit - 1e-6
    ) / len(logs)
    elbow_saturation_fraction = sum(
        1.0 for row in logs if abs(row["motor_elbow_nm"]) >= elbow_motor_limit - 1e-6
    ) / len(logs)

    return {
        "payload_kg": payload_kg,
        "control_mode": control_mode,
        "force_sensor_mode": force_sensor_mode,
        "assist_ratio": assist_ratio,
        "amplification_gain": amplification_gain,
        "motor_response_time_s": motor_response_time_s,
        "duration_s": logs[-1]["time_s"],
        "peak_gravity_shoulder_nm": peak_abs("gravity_shoulder_nm"),
        "peak_gravity_elbow_nm": peak_abs("gravity_elbow_nm"),
        "peak_motor_shoulder_nm": peak_abs("motor_shoulder_nm"),
        "peak_motor_elbow_nm": peak_abs("motor_elbow_nm"),
        "shoulder_motor_saturation_fraction": shoulder_saturation_fraction,
        "elbow_motor_saturation_fraction": elbow_saturation_fraction,
        "peak_measured_shoulder_nm": peak_abs("measured_shoulder_nm"),
        "peak_measured_elbow_nm": peak_abs("measured_elbow_nm"),
        "peak_human_shoulder_nm": peak_human_shoulder,
        "peak_human_elbow_nm": peak_human_elbow,
        "peak_total_shoulder_nm": peak_total_shoulder,
        "peak_total_elbow_nm": peak_total_elbow,
        "shoulder_human_fraction_of_peak_total": shoulder_human_fraction,
        "elbow_human_fraction_of_peak_total": elbow_human_fraction,
        "felt_payload_kg_by_shoulder_peak": payload_kg * shoulder_human_fraction,
        "felt_payload_kg_by_elbow_peak": payload_kg * elbow_human_fraction,
        "shoulder_tracking_rms_deg": shoulder_error_rms,
        "elbow_tracking_rms_deg": elbow_error_rms,
        "shoulder_tracking_max_abs_deg": shoulder_error_max,
        "elbow_tracking_max_abs_deg": elbow_error_max,
        "start_hand_height_m": start_hand_height,
        "end_hand_height_m": end_hand_height,
        "lift_height_m": end_hand_height - start_hand_height,
        "motor_positive_work_j": motor_positive_work_j,
        "human_positive_work_j": human_positive_work_j,
    }


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
