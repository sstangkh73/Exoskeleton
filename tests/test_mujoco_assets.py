import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "arm_exoskeleton_3d.xml"
DESIGN_MODEL_PATH = ROOT / "models" / "arm_exoskeleton_design_v0_1.xml"
DESIGN_CONFIG_PATH = ROOT / "design" / "exo_mechanical_design_v0_1.json"
PRODUCT_CONFIG_PATH = ROOT / "design" / "product_architecture_v0_1.json"


class MuJoCoAssetTests(unittest.TestCase):
    def test_3d_model_contains_required_joints_and_actuators(self) -> None:
        root = ET.parse(MODEL_PATH).getroot()
        names = {element.attrib.get("name") for element in root.iter() if "name" in element.attrib}
        for expected in (
            "shoulder_flexion",
            "elbow_flexion",
            "shoulder_motor",
            "elbow_motor",
            "payload_geom",
            "hand_site",
        ):
            self.assertIn(expected, names)

    def test_3d_model_has_payload_mass(self) -> None:
        root = ET.parse(MODEL_PATH).getroot()
        payload = next(
            element
            for element in root.iter("geom")
            if element.attrib.get("name") == "payload_geom"
        )
        self.assertEqual(payload.attrib["mass"], "5.0")

    def test_design_model_contains_mechanical_layout_elements(self) -> None:
        root = ET.parse(DESIGN_MODEL_PATH).getroot()
        names = {element.attrib.get("name") for element in root.iter() if "name" in element.attrib}
        for expected in (
            "backpack_plate",
            "shoulder_motor_housing",
            "shoulder_transmission_cable",
            "upper_arm_cuff_proximal",
            "upper_arm_cuff_distal",
            "elbow_motor_housing",
            "elbow_drive_plate",
            "forearm_cuff_proximal",
            "forearm_cuff_distal",
            "upper_cuff_force_site",
            "forearm_cuff_force_site",
        ):
            self.assertIn(expected, names)

    def test_design_config_points_to_existing_mujoco_model(self) -> None:
        config = json.loads(DESIGN_CONFIG_PATH.read_text(encoding="utf-8"))
        model_path = ROOT / config["simulation_model"]["mujoco_model_path"]
        self.assertEqual(model_path.resolve(), DESIGN_MODEL_PATH.resolve())
        self.assertTrue(model_path.exists())
        self.assertEqual(config["target_task"]["payload_mass_kg"], 5.0)
        self.assertEqual(config["target_task"]["felt_payload_target_kg"], 2.5)

    def test_product_architecture_points_to_existing_artifacts(self) -> None:
        config = json.loads(PRODUCT_CONFIG_PATH.read_text(encoding="utf-8"))
        for artifact_path in config["artifacts"].values():
            self.assertTrue((ROOT / artifact_path).exists(), artifact_path)
        self.assertEqual(config["power"]["battery_nominal_voltage_v"], 24.0)
        self.assertEqual(config["actuation"]["shoulder"]["transmission_ratio_initial"], 50)
        self.assertEqual(config["actuation"]["elbow"]["transmission_ratio_initial"], 40)


if __name__ == "__main__":
    unittest.main()
