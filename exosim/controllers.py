"""Controllers for simulated human effort and exoskeleton assistance."""

from __future__ import annotations

from dataclasses import dataclass

from .arm import ArmState, Pair, TwoLinkArmModel, add_pair, clamp_pair, scale_pair


@dataclass(frozen=True)
class GravityAssistController:
    """Motor controller that assists by compensating a fraction of gravity torque."""

    assist_ratio: float = 0.4

    def motor_torque(self, model: TwoLinkArmModel, state: ArmState) -> Pair:
        ratio = max(0.0, min(1.0, self.assist_ratio))
        raw = scale_pair(model.gravity_torque(state.q), ratio)
        p = model.params
        return clamp_pair(raw, (p.shoulder_motor_limit_nm, p.elbow_motor_limit_nm))


@dataclass(frozen=True)
class HumanTrackingController:
    """Simple human effort model for following a target joint trajectory."""

    shoulder_kp: float = 90.0
    elbow_kp: float = 60.0
    shoulder_kd: float = 14.0
    elbow_kd: float = 9.0

    def raw_torque(
        self,
        state: ArmState,
        target_q: Pair,
        target_dq: Pair,
        feedforward_torque: Pair,
    ) -> Pair:
        q1, q2 = state.q
        dq1, dq2 = state.dq
        pd = (
            self.shoulder_kp * (target_q[0] - q1)
            + self.shoulder_kd * (target_dq[0] - dq1),
            self.elbow_kp * (target_q[1] - q2)
            + self.elbow_kd * (target_dq[1] - dq2),
        )
        return add_pair(pd, feedforward_torque)

    def torque(
        self,
        model: TwoLinkArmModel,
        state: ArmState,
        target_q: Pair,
        target_dq: Pair,
        feedforward_torque: Pair,
        effort_scale: float = 1.0,
    ) -> Pair:
        raw = scale_pair(
            self.raw_torque(
                state=state,
                target_q=target_q,
                target_dq=target_dq,
                feedforward_torque=feedforward_torque,
            ),
            effort_scale,
        )
        p = model.params
        return clamp_pair(raw, (p.shoulder_human_limit_nm, p.elbow_human_limit_nm))


@dataclass(frozen=True)
class ForceAmplificationController:
    """Motor controller that mirrors measured human torque.

    A gain of 1.0 means the motor tries to add the same joint torque that the
    user is applying. If the sensor truly measures human-only torque, this makes
    the combined torque about 2x the user's torque.
    """

    gain: float = 1.0
    response_time_s: float = 0.03

    def motor_torque(
        self,
        model: TwoLinkArmModel,
        measured_human_torque: Pair,
        previous_motor_torque: Pair,
        dt_s: float,
    ) -> Pair:
        gain = max(0.0, self.gain)
        target = scale_pair(measured_human_torque, gain)

        if self.response_time_s <= 0.0:
            raw = target
        else:
            alpha = max(0.0, min(1.0, dt_s / self.response_time_s))
            raw = (
                previous_motor_torque[0] + (target[0] - previous_motor_torque[0]) * alpha,
                previous_motor_torque[1] + (target[1] - previous_motor_torque[1]) * alpha,
            )

        p = model.params
        return clamp_pair(raw, (p.shoulder_motor_limit_nm, p.elbow_motor_limit_nm))
