"""Planar two-link arm dynamics for exoskeleton prototyping."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Tuple

Pair = Tuple[float, float]


@dataclass(frozen=True)
class ArmParameters:
    """Physical parameters for a human arm plus payload."""

    upper_arm_length_m: float = 0.31
    forearm_length_m: float = 0.34
    upper_arm_mass_kg: float = 2.1
    forearm_mass_kg: float = 1.65
    payload_mass_kg: float = 5.0
    shoulder_damping_nms_per_rad: float = 0.6
    elbow_damping_nms_per_rad: float = 0.35
    gravity_m_s2: float = 9.80665
    shoulder_motor_limit_nm: float = 80.0
    elbow_motor_limit_nm: float = 60.0
    shoulder_human_limit_nm: float = 120.0
    elbow_human_limit_nm: float = 90.0

    @property
    def upper_arm_com_m(self) -> float:
        return 0.5 * self.upper_arm_length_m

    @property
    def forearm_com_m(self) -> float:
        return 0.5 * self.forearm_length_m

    @property
    def upper_arm_inertia_kg_m2(self) -> float:
        return self.upper_arm_mass_kg * self.upper_arm_length_m**2 / 12.0

    @property
    def forearm_inertia_kg_m2(self) -> float:
        return self.forearm_mass_kg * self.forearm_length_m**2 / 12.0

    def with_payload(self, payload_mass_kg: float) -> "ArmParameters":
        return replace(self, payload_mass_kg=payload_mass_kg)


@dataclass(frozen=True)
class ArmState:
    """Joint positions and velocities."""

    shoulder_rad: float
    elbow_rad: float
    shoulder_velocity_rad_s: float = 0.0
    elbow_velocity_rad_s: float = 0.0

    @property
    def q(self) -> Pair:
        return (self.shoulder_rad, self.elbow_rad)

    @property
    def dq(self) -> Pair:
        return (self.shoulder_velocity_rad_s, self.elbow_velocity_rad_s)


class TwoLinkArmModel:
    """Rigid-body dynamics for a planar shoulder-elbow arm."""

    def __init__(self, params: ArmParameters | None = None) -> None:
        self.params = params or ArmParameters()

    def forward_kinematics(self, q: Pair) -> Tuple[float, float, float, float]:
        """Return elbow and hand positions as (elbow_x, elbow_y, hand_x, hand_y)."""

        q1, q2 = q
        p = self.params
        elbow_x = p.upper_arm_length_m * math.cos(q1)
        elbow_y = p.upper_arm_length_m * math.sin(q1)
        hand_x = elbow_x + p.forearm_length_m * math.cos(q1 + q2)
        hand_y = elbow_y + p.forearm_length_m * math.sin(q1 + q2)
        return elbow_x, elbow_y, hand_x, hand_y

    def mass_matrix(self, q: Pair) -> Tuple[Pair, Pair]:
        """Return the 2x2 joint-space inertia matrix."""

        _, q2 = q
        p = self.params
        l1 = p.upper_arm_length_m
        l2 = p.forearm_length_m
        r1 = p.upper_arm_com_m
        r2 = p.forearm_com_m
        m1 = p.upper_arm_mass_kg
        m2 = p.forearm_mass_kg
        mp = p.payload_mass_kg
        i1 = p.upper_arm_inertia_kg_m2
        i2 = p.forearm_inertia_kg_m2
        cos_q2 = math.cos(q2)

        m11 = (
            i1
            + i2
            + m1 * r1**2
            + m2 * (l1**2 + r2**2 + 2.0 * l1 * r2 * cos_q2)
            + mp * (l1**2 + l2**2 + 2.0 * l1 * l2 * cos_q2)
        )
        m12 = i2 + m2 * (r2**2 + l1 * r2 * cos_q2) + mp * (
            l2**2 + l1 * l2 * cos_q2
        )
        m22 = i2 + m2 * r2**2 + mp * l2**2
        return (m11, m12), (m12, m22)

    def coriolis_torque(self, q: Pair, dq: Pair) -> Pair:
        """Return velocity-coupling torque terms C(q, dq)."""

        _, q2 = q
        dq1, dq2 = dq
        p = self.params
        l1 = p.upper_arm_length_m
        l2 = p.forearm_length_m
        r2 = p.forearm_com_m
        m2 = p.forearm_mass_kg
        mp = p.payload_mass_kg
        coupling = (m2 * l1 * r2 + mp * l1 * l2) * math.sin(q2)
        c1 = -coupling * (2.0 * dq1 * dq2 + dq2**2)
        c2 = coupling * dq1**2
        return c1, c2

    def gravity_torque(self, q: Pair) -> Pair:
        """Return torque needed to hold the arm against gravity at q."""

        q1, q2 = q
        p = self.params
        l1 = p.upper_arm_length_m
        l2 = p.forearm_length_m
        r1 = p.upper_arm_com_m
        r2 = p.forearm_com_m
        m1 = p.upper_arm_mass_kg
        m2 = p.forearm_mass_kg
        mp = p.payload_mass_kg
        g = p.gravity_m_s2

        upper_term = (m1 * r1 + m2 * l1 + mp * l1) * math.cos(q1)
        forearm_payload_term = (m2 * r2 + mp * l2) * math.cos(q1 + q2)
        shoulder = g * (upper_term + forearm_payload_term)
        elbow = g * forearm_payload_term
        return shoulder, elbow

    def damping_torque(self, dq: Pair) -> Pair:
        p = self.params
        return (
            p.shoulder_damping_nms_per_rad * dq[0],
            p.elbow_damping_nms_per_rad * dq[1],
        )

    def acceleration(self, state: ArmState, applied_torque: Pair) -> Pair:
        """Compute joint acceleration under applied torque."""

        q = state.q
        dq = state.dq
        (m11, m12), (_, m22) = self.mass_matrix(q)
        c1, c2 = self.coriolis_torque(q, dq)
        g1, g2 = self.gravity_torque(q)
        d1, d2 = self.damping_torque(dq)
        rhs1 = applied_torque[0] - c1 - g1 - d1
        rhs2 = applied_torque[1] - c2 - g2 - d2

        det = m11 * m22 - m12 * m12
        if det <= 0.0:
            raise ValueError(f"Mass matrix is not positive definite: det={det}")

        ddq1 = (m22 * rhs1 - m12 * rhs2) / det
        ddq2 = (-m12 * rhs1 + m11 * rhs2) / det
        return ddq1, ddq2

    def step(self, state: ArmState, applied_torque: Pair, dt_s: float) -> ArmState:
        """Advance the model by one semi-implicit Euler step."""

        ddq1, ddq2 = self.acceleration(state, applied_torque)
        dq1 = state.shoulder_velocity_rad_s + ddq1 * dt_s
        dq2 = state.elbow_velocity_rad_s + ddq2 * dt_s
        q1 = state.shoulder_rad + dq1 * dt_s
        q2 = state.elbow_rad + dq2 * dt_s
        return ArmState(q1, q2, dq1, dq2)


def clamp(value: float, limit: float) -> float:
    if limit < 0.0:
        raise ValueError("limit must be non-negative")
    return max(-limit, min(limit, value))


def clamp_pair(values: Pair, limits: Pair) -> Pair:
    return clamp(values[0], limits[0]), clamp(values[1], limits[1])


def add_pair(a: Pair, b: Pair) -> Pair:
    return a[0] + b[0], a[1] + b[1]


def subtract_pair(a: Pair, b: Pair) -> Pair:
    return a[0] - b[0], a[1] - b[1]


def scale_pair(values: Pair, factor: float) -> Pair:
    return values[0] * factor, values[1] * factor
