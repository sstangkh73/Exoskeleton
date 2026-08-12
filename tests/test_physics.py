import math
import unittest

from exosim.arm import ArmParameters, TwoLinkArmModel, subtract_pair
from exosim.controllers import ForceAmplificationController, GravityAssistController
from exosim.scenario import ScenarioConfig, simulate_lift


class PhysicsModelTests(unittest.TestCase):
    def test_forward_kinematics_straight_arm(self) -> None:
        params = ArmParameters(payload_mass_kg=0.0)
        model = TwoLinkArmModel(params)
        _, _, hand_x, hand_y = model.forward_kinematics((0.0, 0.0))
        self.assertAlmostEqual(
            hand_x, params.upper_arm_length_m + params.forearm_length_m, places=9
        )
        self.assertAlmostEqual(hand_y, 0.0, places=9)

    def test_payload_increases_elbow_gravity_torque(self) -> None:
        no_payload = TwoLinkArmModel(ArmParameters(payload_mass_kg=0.0))
        with_payload = TwoLinkArmModel(ArmParameters(payload_mass_kg=5.0))
        base_elbow = no_payload.gravity_torque((0.0, 0.0))[1]
        loaded_elbow = with_payload.gravity_torque((0.0, 0.0))[1]
        expected_added = 5.0 * with_payload.params.gravity_m_s2 * with_payload.params.forearm_length_m
        self.assertAlmostEqual(loaded_elbow - base_elbow, expected_added, places=9)

    def test_mass_matrix_is_symmetric_positive(self) -> None:
        model = TwoLinkArmModel(ArmParameters(payload_mass_kg=5.0))
        (m11, m12), (m21, m22) = model.mass_matrix((math.radians(35.0), math.radians(55.0)))
        self.assertAlmostEqual(m12, m21, places=12)
        self.assertGreater(m11, 0.0)
        self.assertGreater(m22, 0.0)
        self.assertGreater(m11 * m22 - m12 * m21, 0.0)

    def test_gravity_assist_reduces_required_human_hold_torque(self) -> None:
        model = TwoLinkArmModel(ArmParameters(payload_mass_kg=5.0))
        state_q = (math.radians(20.0), math.radians(60.0))
        gravity = model.gravity_torque(state_q)
        fake_state = type("State", (), {"q": state_q})()
        motor = GravityAssistController(assist_ratio=0.4).motor_torque(model, fake_state)
        human = subtract_pair(gravity, motor)
        self.assertAlmostEqual(human[0], gravity[0] * 0.6, places=9)
        self.assertAlmostEqual(human[1], gravity[1] * 0.6, places=9)

    def test_lift_simulation_generates_metrics(self) -> None:
        logs, metrics = simulate_lift(ScenarioConfig(duration_s=0.1, dt_s=0.01))
        self.assertEqual(len(logs), 11)
        self.assertIn("peak_human_shoulder_nm", metrics)
        self.assertGreater(metrics["peak_human_shoulder_nm"], 0.0)

    def test_force_amplification_gain_one_mirrors_human_torque(self) -> None:
        model = TwoLinkArmModel(ArmParameters(payload_mass_kg=5.0))
        controller = ForceAmplificationController(gain=1.0, response_time_s=0.0)
        motor = controller.motor_torque(
            model=model,
            measured_human_torque=(10.0, -4.0),
            previous_motor_torque=(0.0, 0.0),
            dt_s=0.01,
        )
        self.assertEqual(motor, (10.0, -4.0))

    def test_force_amplification_reduces_human_peak_torque(self) -> None:
        _, baseline = simulate_lift(
            ScenarioConfig(
                control_mode="force_amp",
                amplification_gain=0.0,
                motor_response_time_s=0.0,
                duration_s=0.5,
                dt_s=0.01,
            )
        )
        _, amplified = simulate_lift(
            ScenarioConfig(
                control_mode="force_amp",
                amplification_gain=1.0,
                motor_response_time_s=0.0,
                duration_s=0.5,
                dt_s=0.01,
            )
        )
        self.assertLess(
            amplified["peak_human_shoulder_nm"],
            baseline["peak_human_shoulder_nm"] * 0.6,
        )

    def test_combined_sensor_creates_feedback_risk(self) -> None:
        _, human_only = simulate_lift(
            ScenarioConfig(
                control_mode="force_amp",
                force_sensor_mode="human_only",
                amplification_gain=1.0,
                motor_response_time_s=0.0,
                duration_s=0.5,
                dt_s=0.01,
            )
        )
        _, combined = simulate_lift(
            ScenarioConfig(
                control_mode="force_amp",
                force_sensor_mode="combined",
                amplification_gain=1.0,
                motor_response_time_s=0.0,
                duration_s=0.5,
                dt_s=0.01,
            )
        )
        self.assertGreater(
            combined["peak_motor_shoulder_nm"],
            human_only["peak_motor_shoulder_nm"] * 2.0,
        )


if __name__ == "__main__":
    unittest.main()
