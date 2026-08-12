"""Render a single preview image of the 3D MuJoCo arm model."""

from __future__ import annotations

import argparse
from pathlib import Path

from .mujoco_simulate import DEFAULT_MODEL, import_mujoco, load_model, set_joint_state
from .scenario import deg_to_rad


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render the 3D arm model to a PNG.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--payload-kg", type=float, default=5.0)
    parser.add_argument("--shoulder-deg", type=float, default=45.0)
    parser.add_argument("--elbow-deg", type=float, default=60.0)
    parser.add_argument("--output", type=Path, default=Path("outputs/arm_3d_preview.png"))
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    mujoco = import_mujoco()

    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Pillow is needed to save preview PNGs. Install it with:\n"
            "  python -m pip install -r requirements.txt"
        ) from exc

    model = load_model(mujoco, args.model, args.payload_kg)
    data = mujoco.MjData(model)
    set_joint_state(data, "shoulder_flexion", deg_to_rad(args.shoulder_deg))
    set_joint_state(data, "elbow_flexion", deg_to_rad(args.elbow_deg))
    mujoco.mj_forward(model, data)

    camera = mujoco.MjvCamera()
    camera.lookat[:] = [0.35, 0.0, 1.55]
    camera.distance = 1.1
    camera.azimuth = 125
    camera.elevation = -12

    renderer = mujoco.Renderer(model, height=args.height, width=args.width)
    renderer.update_scene(data, camera=camera)
    image = renderer.render()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(args.output)
    renderer.close()
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
