# 3D Simulation Plan

The 3D simulator starts with a minimal MuJoCo model instead of a detailed CAD
model. The point is to preserve the physics questions from the 2D simulator:

- What torque does each joint need during a lift?
- How much torque does the human provide?
- How much torque does the motor provide?
- Does force amplification still make 5 kg feel like about 2.5 kg once motor lag
  and actuator limits exist?

## First 3D Model

`models/arm_exoskeleton_3d.xml` contains:

- fixed torso/shoulder anchor
- upper-arm capsule, mass 2.1 kg
- forearm capsule, mass 1.65 kg
- 5 kg payload at the hand
- shoulder and elbow hinge joints
- shoulder and elbow motor actuators
- simple exoskeleton bars for visual orientation

The first version is still constrained to the sagittal lifting plane. That is
intentional: it gives real 3D rigid-body physics while keeping the control
problem close to the validated 2D model.

## Running

Install MuJoCo first:

```powershell
python -m pip install -r requirements.txt
```

Run headless and write CSV:

```powershell
python -m exosim.mujoco_simulate --control-mode force_amp --payload-kg 5 --felt-payload-kg 2.5 --output outputs\lift_3d_force_amp.csv
```

Open the viewer:

```powershell
python -m exosim.mujoco_simulate --control-mode force_amp --payload-kg 5 --felt-payload-kg 2.5 --viewer
```

Render a static preview image:

```powershell
python -m exosim.render_mujoco_preview --output outputs\arm_3d_preview.png
```

## Control Mapping

The runner separates human and motor torque:

```text
human torque -> data.qfrc_applied at shoulder/elbow dofs
motor torque -> actuator ctrl for shoulder_motor/elbow_motor
```

This separation matters for the project's key control problem. If a real sensor
measures only human torque, force amplification can behave like:

```text
motor = gain * human
gain = 1.0 -> human supplies about 50% of total joint torque
```

If the sensor measures combined human plus motor torque, that can create
positive feedback. The next experiment should explicitly simulate that bad
sensor model with delay/noise.

Run the bad-sensor variant in 3D:

```powershell
python -m exosim.mujoco_simulate --control-mode force_amp --force-sensor-mode combined --payload-kg 5 --felt-payload-kg 2.5 --output outputs\lift_3d_bad_sensor.csv
```

Run the full 3D comparison table:

```powershell
python scripts\run_3d_sensor_feedback_experiment.py
```
