# Exoskeleton Arm Physics Simulator

Simulation-first prototype for an assistive arm exoskeleton. The current scope is
a planar two-link arm: shoulder, elbow, upper arm, forearm, and a payload held at
the hand.

The goal is to answer engineering questions before building hardware:

- How much shoulder and elbow torque is required to hold or lift a payload?
- How much motor torque is needed for a given assist ratio?
- How much human torque remains after assistance?
- What torque peaks appear during a simple lift trajectory?

## Model

The simulator uses standard two-link rigid-body dynamics:

```text
M(q) q_ddot + C(q, q_dot) + G(q) + D q_dot = tau_human + tau_motor
```

Coordinate convention:

- `shoulder_rad` is the upper-arm angle measured from horizontal.
- `elbow_rad` is the forearm angle relative to the upper arm.
- `0, 0` means the whole arm is straight forward and horizontal.
- Positive angles rotate upward.

The simulator currently supports two assist modes.

### Gravity Compensation

This mode uses the model's gravity estimate and asks the motor to carry a fixed
fraction of it:

```text
tau_motor = assist_ratio * G(q)
tau_human = tracking_PD + remaining_gravity
```

This is useful for understanding joint torque requirements and motor sizing.

### Force Amplification

This mode follows the first target behavior for the project: make a 5 kg payload
feel like 2.5 kg by having the motor mirror the user's measured effort.

```text
tau_motor = gain * measured_tau_human
tau_total = tau_human + tau_motor
```

For example:

```text
gain = 1.0
human applies 10 Nm
motor adds 10 Nm
total joint torque is 20 Nm
```

If `gain = 1.0`, the human contributes about half of the total joint torque, so
a 5 kg payload has a first-order felt-load estimate of 2.5 kg. The simulation
assumes the sensor can measure human-only torque. If the sensor accidentally
measures combined human + motor torque, this controller can create positive
feedback and become unstable. That is one of the main problems to explore before
hardware.

## Quick Start

Run one lift simulation:

```powershell
python -m exosim.simulate --payload-kg 5 --assist 0.4 --output outputs/lift_5kg_40assist.csv
```

Run the first force-amplification target, where 5 kg should feel like 2.5 kg:

```powershell
python -m exosim.simulate --payload-kg 5 --control-mode force_amp --felt-payload-kg 2.5 --motor-response-time-s 0 --output outputs/lift_5kg_feels_2p5kg_force_amp.csv
```

Run the bad-sensor version where the controller reads human + previous motor
torque:

```powershell
python -m exosim.simulate --payload-kg 5 --control-mode force_amp --force-sensor-mode combined --felt-payload-kg 2.5 --motor-response-time-s 0 --output outputs\lift_bad_sensor.csv
```

Run an assist-ratio sweep:

```powershell
python scripts/run_assist_sweep.py
```

Run a force-amplification gain sweep:

```powershell
python scripts/run_force_amplification_sweep.py
```

Run the sensor feedback comparison:

```powershell
python scripts/run_sensor_feedback_experiment.py
```

Run the same sensor comparison through MuJoCo 3D:

```powershell
.\.venv\Scripts\python.exe scripts\run_3d_sensor_feedback_experiment.py
```

Run the first 3D MuJoCo simulation:

```powershell
python -m pip install -r requirements.txt
python -m exosim.mujoco_simulate --control-mode force_amp --payload-kg 5 --felt-payload-kg 2.5 --output outputs\lift_3d_force_amp.csv
```

Add `--viewer` to watch the MuJoCo scene if the local graphics environment
supports it.

Render a static 3D preview:

```powershell
python -m exosim.render_mujoco_preview --output outputs\arm_3d_preview.png
```

Read the first mechanical layout spec:

```text
docs/mechanical_design_v0_1.th.md
design/exo_mechanical_design_v0_1.json
models/arm_exoskeleton_design_v0_1.xml
```

Read the product-level engineering blueprint:

```text
outputs/exo_product_blueprint_v0_1.svg
outputs/exo_product_blueprint_v0_1.png
docs/product_engineering_blueprint_v0_1.th.md
design/product_architecture_v0_1.json
```

Read fly-by-wire papers and translation notes for the exoskeleton control architecture:

```text
docs/fly_by_wire_literature_review_2026-07-03.th.md
```

Run tests:

```powershell
python -m unittest discover -s tests
```

## Next Steps

1. Validate anthropometric parameters against a target user profile.
2. Test force amplification with motor lag, torque limits, and noisy sensors.
3. Add torque limits and thermal/load curves for candidate motors.
4. Add contact constraints for a carried object or handle.
5. Add a deliberately bad sensor model that reads human + motor torque to study
   force-amplification instability.
