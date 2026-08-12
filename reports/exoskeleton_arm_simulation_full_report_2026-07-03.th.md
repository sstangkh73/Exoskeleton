# รายงานฉบับเต็ม: การจำลองแขน Exoskeleton ช่วยยกของด้วยการขยายแรงแบบ Force Amplification

วันที่จัดทำ: 3 กรกฎาคม 2026  
โครงการ: Exoskeleton Arm Physics Simulator  
ตำแหน่งไฟล์หลัก: `C:\Exoskeleton`

## บทคัดย่อ

รายงานนี้นำเสนอการพัฒนาและทดลองระบบจำลองแขน exoskeleton สำหรับช่วยยกของ โดยเริ่มจากเป้าหมายเชิงวิศวกรรมที่ชัดเจนคือทำให้การยกของมวล 5 kg ให้ผู้ใช้รู้สึกใกล้เคียงกับการยกของ 2.5 kg หรือกล่าวอีกแบบคือให้ระบบช่วยรับภาระประมาณครึ่งหนึ่งของแรงบิดที่ต้องใช้ในการยก

โครงการนี้ยังไม่สร้างฮาร์ดแวร์จริง แต่เริ่มจาก simulation-first เพื่อศึกษาฟิสิกส์ แรงบิดของข้อต่อ การทำงานของมอเตอร์ และความเสี่ยงด้านการควบคุมก่อน ในระยะแรกได้พัฒนาแบบจำลอง 2D ของแขนสองท่อน ได้แก่ หัวไหล่ ข้อศอก ท่อนแขนบน ท่อนปลายแขน และ payload ที่มือ จากนั้นขยายเป็นแบบจำลอง 3D ด้วย MuJoCo โดยแยกแรงบิดจากมนุษย์และแรงบิดจากมอเตอร์ออกจากกันอย่างชัดเจน

ผลการทดลองหลักพบว่า ในกรณีอุดมคติที่ sensor อ่านแรงจากมนุษย์อย่างเดียว (`human_only`) ระบบ force amplification ที่ gain = 1.0 สามารถทำให้ 5 kg มีค่าประมาณน้ำหนักที่ผู้ใช้รู้สึกเป็น 2.50 kg ได้ตามเป้าหมายใน 2D และ 3D simulation แต่เมื่อจำลองกรณี sensor ที่ไม่ดี ซึ่งอ่านแรงรวมของมนุษย์และมอเตอร์ (`combined`) ระบบเกิด positive feedback จนมอเตอร์ชนขีดจำกัด 80 Nm ที่หัวไหล่ และ tracking error เพิ่มขึ้นอย่างมีนัยสำคัญ

ข้อค้นพบสำคัญคือ แนวคิด “มนุษย์ออกแรงเท่าไร มอเตอร์ช่วยเท่านั้น” มีความเป็นไปได้ใน simulation แต่ความปลอดภัยของระบบขึ้นอยู่กับการวัดแรงที่ถูกต้องมาก หาก sensor แยกแรงมนุษย์ออกจากแรงมอเตอร์ไม่ได้ ระบบอาจช่วยมากเกินไป สั่น หรือผลักแขนออกจาก trajectory ที่ต้องการ

## 1. ที่มาและความสำคัญ

การยกของเป็นกิจกรรมที่สร้างภาระต่อกล้ามเนื้อแขน ไหล่ หลัง และข้อต่อ โดยเฉพาะงานซ้ำ ๆ หรือการยกของที่มีน้ำหนักปานกลางถึงมาก Exoskeleton เป็นแนวทางหนึ่งที่สามารถช่วยลดภาระของผู้ใช้ได้ โดยใช้โครงสร้างกลไกและ actuator เพื่อช่วยออกแรงตามการเคลื่อนไหวของร่างกาย

อย่างไรก็ตาม การสร้างฮาร์ดแวร์จริงตั้งแต่ต้นมีความเสี่ยงหลายด้าน เช่น การเลือกมอเตอร์ผิดขนาด การควบคุมไม่เสถียร การช่วยแรงผิดจังหวะ หรือการทำให้ผู้ใช้ได้รับแรงเกินจำเป็น ดังนั้นโครงการนี้จึงเริ่มจากการจำลองฟิสิกส์ก่อน เพื่อให้สามารถตอบคำถามพื้นฐานได้ เช่น

- ต้องใช้แรงบิดที่หัวไหล่และข้อศอกเท่าไรในการยกของ 5 kg
- หากต้องการให้ 5 kg รู้สึกเหมือน 2.5 kg มอเตอร์ต้องช่วยแรงบิดประมาณเท่าไร
- การควบคุมแบบมอเตอร์ช่วยตามแรงมนุษย์มีปัญหาอะไรบ้าง
- sensor แบบใดมีความเสี่ยงต่อ positive feedback
- ก่อนสร้าง hardware ควรทดสอบความเสี่ยงใดใน simulation ก่อน

## 2. วัตถุประสงค์

1. พัฒนาแบบจำลองฟิสิกส์ของแขนที่ใช้ศึกษาแรงบิดขณะยกของ
2. จำลองระบบช่วยแรงที่ทำให้ของ 5 kg รู้สึกใกล้เคียงกับ 2.5 kg
3. เปรียบเทียบการควบคุมแบบ gravity compensation และ force amplification
4. ทดสอบปัญหา sensor feedback เมื่อมอเตอร์ช่วยตามแรงที่วัดได้
5. สร้างฐาน simulation 3D ด้วย MuJoCo สำหรับต่อยอดไปสู่การออกแบบ actuator, sensor และ controller ที่ปลอดภัยขึ้น

## 3. ขอบเขตของโครงการปัจจุบัน

โครงการในระยะนี้เป็นการจำลองเท่านั้น ยังไม่มีฮาร์ดแวร์จริง ไม่มี sensor จริง และยังไม่มีการทดสอบกับมนุษย์จริง ผลลัพธ์ทั้งหมดจึงควรตีความเป็นผลจากแบบจำลองภายใต้สมมติฐานที่กำหนด ไม่ใช่ผลยืนยันว่าระบบจริงจะทำงานได้ปลอดภัยทันที

ขอบเขตที่ทำแล้ว:

- แบบจำลองแขน 2D แบบสองข้อต่อ
- แบบจำลอง 3D ด้วย MuJoCo
- payload ที่มือ ปรับมวลได้ผ่าน CLI
- motor actuator ที่หัวไหล่และข้อศอก
- โหมดควบคุม `gravity` และ `force_amp`
- โหมด sensor `human_only` และ `combined`
- การบันทึก CSV และสรุป metrics
- การ render ภาพ preview ของโมเดล 3D

ขอบเขตที่ยังไม่ทำ:

- ฮาร์ดแวร์จริง
- sensor จริง เช่น force sensor, torque sensor, EMG หรือ strain gauge
- ข้อต่อไหล่แบบ 3 degree-of-freedom
- การเคลื่อนไหวนอกระนาบ sagittal plane
- contact model ระหว่างแขนมนุษย์กับโครง exoskeleton
- controller ด้านความปลอดภัยระดับ production เช่น impedance control, emergency stop, torque ramp, watchdog

## 4. แนวคิดทางฟิสิกส์และการควบคุม

### 4.1 แรงและแรงบิด

แนวคิดเริ่มต้นของโครงการคือ “ถ้าแขนออกแรง 10 N มอเตอร์ช่วยอีก 10 N แรงรวมเป็น 20 N” สำหรับระบบแขน exoskeleton จำเป็นต้องแปลงแนวคิดนี้เป็นแรงบิดที่ข้อต่อ เนื่องจากมอเตอร์ไม่ได้ช่วยเพียงแรงเชิงเส้นที่มือ แต่ช่วยหมุนข้อต่อ เช่น หัวไหล่และข้อศอก

ความสัมพันธ์พื้นฐานคือ:

```text
torque = force x moment_arm
```

ดังนั้นใน simulation นี้จึงใช้หน่วยหลักเป็น `Nm` หรือ Newton-meter สำหรับแรงบิดที่หัวไหล่และข้อศอก

### 4.2 แบบจำลองแขน 2D

แบบจำลอง 2D ใช้ rigid-body dynamics ของแขนสองท่อน:

```text
M(q) q_ddot + C(q, q_dot) + G(q) + D q_dot = tau_human + tau_motor
```

โดยที่:

- `M(q)` คือ mass matrix
- `C(q, q_dot)` คือแรงบิดจาก coriolis/centrifugal terms
- `G(q)` คือแรงบิดจากแรงโน้มถ่วง
- `D q_dot` คือ damping
- `tau_human` คือแรงบิดที่มนุษย์ออก
- `tau_motor` คือแรงบิดที่มอเตอร์ช่วย

### 4.3 Gravity Compensation

โหมดนี้ให้มอเตอร์ช่วยรับแรงโน้มถ่วงบางส่วน:

```text
tau_motor = assist_ratio * G(q)
```

หาก `assist_ratio = 0.4` มอเตอร์จะช่วยรับแรงบิดจาก gravity ประมาณ 40% และมนุษย์รับส่วนที่เหลือพร้อมแรงควบคุมเพื่อทำตาม trajectory

### 4.4 Force Amplification

โหมดนี้ตรงกับแนวคิดหลักของโครงการ:

```text
tau_motor = gain * measured_tau
tau_total = tau_human + tau_motor
```

หาก sensor วัดแรงบิดจากมนุษย์ได้จริง และตั้ง `gain = 1.0`:

```text
human torque = 10 Nm
motor torque = 10 Nm
total torque = 20 Nm
```

ในกรณีนี้มนุษย์รับภาระประมาณครึ่งหนึ่งของแรงบิดรวม จึงคาดหวังว่า payload 5 kg จะรู้สึกใกล้เคียงกับ 2.5 kg

### 4.5 ปัญหา Sensor Feedback

จุดเสี่ยงสำคัญคือ sensor อ่านค่าอะไร หาก sensor อ่านเฉพาะแรงจากมนุษย์ ระบบจะมีพฤติกรรมตามที่ตั้งใจ แต่หาก sensor อ่านแรงรวมของมนุษย์และมอเตอร์ ระบบจะเกิดวงจรป้อนกลับ:

```text
motor ช่วยมากขึ้น -> sensor อ่านแรงรวมมากขึ้น -> motor ช่วยมากขึ้นอีก
```

ใน simulation นี้จึงจำลอง sensor สองแบบ:

- `human_only`: sensor อ่านแรงบิดจากมนุษย์เท่านั้น
- `combined`: sensor อ่านแรงบิดจากมนุษย์รวมกับแรงบิดมอเตอร์รอบก่อนหน้า

โหมด `combined` เป็นการจำลองกรณีผิดพลาดเพื่อดูความเสี่ยงก่อนสร้างฮาร์ดแวร์จริง

## 5. เครื่องมือและโครงสร้างระบบ

### 5.1 ภาษาและเครื่องมือ

- Python สำหรับ simulation runner และการคำนวณ
- MuJoCo สำหรับ 3D rigid-body physics
- MJCF XML สำหรับกำหนดโมเดล 3D
- CSV สำหรับบันทึก time series และ summary metrics
- Unit tests ด้วย `unittest`

MuJoCo ถูกเลือกเพราะเป็น physics engine แบบ open source ที่เหมาะกับ robotics, biomechanics และระบบ articulated body อีกทั้ง Python binding ทางการรองรับการโหลดโมเดลจาก XML และการจำลอง step-by-step

### 5.2 โครงสร้างไฟล์สำคัญ

```text
C:\Exoskeleton
├── exosim
│   ├── arm.py
│   ├── controllers.py
│   ├── scenario.py
│   ├── simulate.py
│   ├── mujoco_simulate.py
│   └── render_mujoco_preview.py
├── models
│   └── arm_exoskeleton_3d.xml
├── scripts
│   ├── run_assist_sweep.py
│   ├── run_force_amplification_sweep.py
│   ├── run_sensor_feedback_experiment.py
│   └── run_3d_sensor_feedback_experiment.py
├── outputs
│   ├── assist_sweep_summary.csv
│   ├── force_amp_sweep_summary.csv
│   ├── sensor_feedback_summary.csv
│   ├── sensor_feedback_3d_summary.csv
│   └── arm_3d_preview.png
└── tests
    ├── test_physics.py
    └── test_mujoco_assets.py
```

### 5.3 โมเดล 3D

โมเดล 3D อยู่ที่:

```text
models/arm_exoskeleton_3d.xml
```

องค์ประกอบหลัก:

- torso anchor แบบ fixed
- upper arm เป็น capsule มวล 2.1 kg
- forearm เป็น capsule มวล 1.65 kg
- payload เป็น box ที่มือ มวลเริ่มต้น 5 kg
- shoulder hinge
- elbow hinge
- shoulder motor actuator
- elbow motor actuator
- exoskeleton bars สำหรับมอง orientation ของระบบ

ภาพ preview:

```text
outputs/arm_3d_preview.png
```

## 6. วิธีดำเนินการทดลอง

### 6.1 การทดลอง Gravity Compensation

เป้าหมายคือดูว่าเมื่อเพิ่ม `assist_ratio` แล้ว peak human torque ลดลงหรือไม่ โดยทดสอบ:

```text
assist_ratio = 0.0, 0.2, 0.4, 0.6, 0.8
```

คำสั่ง:

```powershell
python scripts/run_assist_sweep.py
```

### 6.2 การทดลอง Force Amplification Gain Sweep

เป้าหมายคือดูความสัมพันธ์ระหว่าง gain กับ felt payload estimate โดยทดสอบ:

```text
gain = 0.0, 0.5, 1.0, 1.5, 2.0
```

คำสั่ง:

```powershell
python scripts/run_force_amplification_sweep.py
```

### 6.3 การทดลอง Sensor Feedback ใน 2D

เป้าหมายคือเปรียบเทียบ `human_only` กับ `combined` ภายใต้ motor response time ต่างกัน:

```text
motor_response_time_s = 0.0, 0.03, 0.08
```

คำสั่ง:

```powershell
python scripts/run_sensor_feedback_experiment.py
```

### 6.4 การทดลอง Sensor Feedback ใน 3D MuJoCo

เป้าหมายคือยืนยัน pattern เดียวกันใน 3D rigid-body physics:

```powershell
.\.venv\Scripts\python.exe scripts\run_3d_sensor_feedback_experiment.py
```

### 6.5 Metrics ที่ใช้ประเมิน

Metrics หลัก:

- `peak_human_shoulder_nm`: แรงบิดสูงสุดที่มนุษย์ต้องออกที่หัวไหล่
- `peak_motor_shoulder_nm`: แรงบิดสูงสุดที่มอเตอร์ช่วยที่หัวไหล่
- `felt_payload_kg_by_shoulder_peak`: ค่าประมาณ payload ที่ผู้ใช้รู้สึกจากสัดส่วนแรงบิด
- `shoulder_tracking_max_abs_deg`: error สูงสุดระหว่างมุมเป้าหมายกับมุมจริง
- `shoulder_motor_saturation_fraction`: สัดส่วนเวลาที่มอเตอร์หัวไหล่ชน torque limit

ข้อควรระวัง: `felt_payload_kg_by_shoulder_peak` เป็นค่าประมาณเชิงกลศาสตร์จากสัดส่วน peak torque ไม่ใช่ผล psychophysics จากผู้ใช้จริง

## 7. ผลการทดลอง

### 7.1 ผล Gravity Compensation ใน 2D

ไฟล์ผลลัพธ์:

```text
outputs/assist_sweep_summary.csv
```

| assist ratio | peak human shoulder (Nm) | peak motor shoulder (Nm) | peak human elbow (Nm) | peak motor elbow (Nm) |
|---:|---:|---:|---:|---:|
| 0% | 23.30 | 0.00 | 7.31 | 0.00 |
| 20% | 18.79 | 4.52 | 5.93 | 1.38 |
| 40% | 14.29 | 9.04 | 4.55 | 2.76 |
| 60% | 9.80 | 13.57 | 3.17 | 4.14 |
| 80% | 5.31 | 18.09 | 1.78 | 5.53 |

ผลนี้แสดงว่าเมื่อเพิ่ม assist ratio แรงบิดที่มนุษย์ต้องออกลดลงตามคาด และแรงบิดจากมอเตอร์เพิ่มขึ้นตามสัดส่วน

### 7.2 ผล Force Amplification Gain Sweep ใน 2D

ไฟล์ผลลัพธ์:

```text
outputs/force_amp_sweep_summary.csv
```

| amplification gain | felt payload by shoulder peak (kg) | peak human shoulder (Nm) | peak motor shoulder (Nm) |
|---:|---:|---:|---:|
| 0.0 | 5.00 | 23.30 | 0.00 |
| 0.5 | 3.33 | 15.53 | 7.77 |
| 1.0 | 2.50 | 11.65 | 11.65 |
| 1.5 | 2.00 | 9.32 | 13.98 |
| 2.0 | 1.67 | 7.77 | 15.53 |

เมื่อ `gain = 1.0` แรงบิดมนุษย์และแรงบิดมอเตอร์เท่ากัน ทำให้ payload 5 kg มีค่าประมาณที่ผู้ใช้รู้สึกเป็น 2.50 kg ตามเป้าหมายเริ่มต้น

### 7.3 ผล Sensor Feedback ใน 2D

ไฟล์ผลลัพธ์:

```text
outputs/sensor_feedback_summary.csv
```

| sensor mode | motor lag (ms) | felt shoulder (kg) | peak motor shoulder (Nm) | max shoulder error (deg) |
|---|---:|---:|---:|---:|
| human_only | 0 | 2.50 | 11.65 | 0.47 |
| human_only | 30 | 2.63 | 12.17 | 0.81 |
| human_only | 80 | 2.70 | 13.06 | 1.92 |
| combined | 0 | 0.80 | 80.00 | 12.07 |
| combined | 30 | 1.99 | 80.00 | 29.60 |
| combined | 80 | 2.54 | 80.00 | 58.77 |

ผลสำคัญ:

- `human_only` ทำงานใกล้เป้าหมาย และ tracking error ยังต่ำ
- `combined` ทำให้มอเตอร์หัวไหล่ชน limit 80 Nm ทุกกรณี
- เมื่อ motor lag เพิ่มขึ้นใน `combined` tracking error ยิ่งสูงขึ้น
- ค่า felt payload ใน `combined` อาจดูเหมือนเบาลง แต่เป็นผลลวงจากการที่มอเตอร์ช่วยเกินและชน limit ไม่ใช่ระบบช่วยแรงที่ควบคุมได้ดี

### 7.4 ผล Sensor Feedback ใน 3D MuJoCo

ไฟล์ผลลัพธ์:

```text
outputs/sensor_feedback_3d_summary.csv
```

| sensor mode | motor lag (ms) | peak motor shoulder (Nm) | shoulder saturation | max shoulder error (deg) |
|---|---:|---:|---:|---:|
| human_only | 0 | 14.48 | 0.00% | 4.29 |
| human_only | 30 | 14.50 | 0.00% | 4.23 |
| human_only | 80 | 14.95 | 0.00% | 4.13 |
| combined | 0 | 80.00 | 31.61% | 12.15 |
| combined | 30 | 80.00 | 28.79% | 21.99 |
| combined | 80 | 80.00 | 6.32% | 31.12 |

ผล 3D ยืนยัน pattern เดียวกับ 2D:

- `human_only` ไม่ชน motor limit
- `combined` ชน motor limit ที่หัวไหล่ 80 Nm
- tracking error ของ `combined` สูงกว่า `human_only` อย่างชัดเจน
- motor lag ยิ่งมาก error ยิ่งรุนแรงใน 3D เช่นกัน

## 8. การวิเคราะห์ผล

### 8.1 เป้าหมาย “5 kg ให้เหมือน 2.5 kg” ทำได้ใน simulation

ในโหมด force amplification เมื่อ sensor อ่านแรงมนุษย์ได้โดยตรง และตั้ง `gain = 1.0` ระบบสามารถแบ่งภาระระหว่างมนุษย์และมอเตอร์ได้ประมาณครึ่งต่อครึ่ง ผล 2D แสดงว่า:

```text
peak human shoulder = 11.65 Nm
peak motor shoulder = 11.65 Nm
felt payload estimate = 2.50 kg
```

ผลนี้ตรงกับเป้าหมายเริ่มต้นของโครงการ และเป็นหลักฐานเชิง simulation ว่าแนวคิด force amplification มีเหตุผลทางฟิสิกส์

### 8.2 ปัญหาหลักไม่ใช่แค่มอเตอร์แรงพอ แต่คือ sensor อ่านแรงอะไร

การทดลอง `combined` แสดงให้เห็นว่าหาก sensor อ่านแรงรวมที่มีแรงมอเตอร์ปนอยู่ ระบบจะเข้าใจผิดว่ามนุษย์กำลังออกแรงมากขึ้น แล้วสั่งให้มอเตอร์ช่วยเพิ่มขึ้นอีก ทำให้เกิด positive feedback

ใน 2D:

```text
combined 0 ms -> peak motor shoulder = 80.00 Nm
```

ใน 3D:

```text
combined 0 ms -> peak motor shoulder = 80.00 Nm
shoulder saturation = 31.61%
```

นี่หมายความว่าระบบไม่ได้แค่ช่วยมากขึ้น แต่ชนขีดจำกัดมอเตอร์ ซึ่งเป็นสัญญาณอันตรายสำหรับฮาร์ดแวร์จริง

### 8.3 Motor lag ส่งผลต่อเสถียรภาพ

ใน `human_only` motor lag ทำให้ felt payload estimate เพิ่มจาก 2.50 kg เป็นประมาณ 2.63-2.70 kg ใน 2D แปลว่าผู้ใช้ต้องรับภาระเพิ่มขึ้นเล็กน้อยเพราะมอเตอร์ตอบสนองช้า

ใน `combined` motor lag ทำให้ tracking error เพิ่มมาก เช่น:

```text
2D combined 80 ms -> max shoulder error = 58.77 deg
3D combined 80 ms -> max shoulder error = 31.12 deg
```

ดังนั้นระบบจริงควรมีการวิเคราะห์ latency และ bandwidth ของ sensor-controller-motor loop อย่างจริงจัง

### 8.4 2D และ 3D ให้ข้อสรุปเชิงแนวโน้มตรงกัน

แม้ค่า absolute torque ใน 2D และ 3D ต่างกันบ้าง เนื่องจากโมเดล inertial และ geometry ไม่เหมือนกันทั้งหมด แต่ pattern สำคัญตรงกัน:

- force amplification แบบ sensor ดีทำงานได้
- sensor แบบ combined ทำให้ feedback
- มอเตอร์ชน torque limit
- tracking error เพิ่มขึ้น

การที่ผล 2D และ 3D สอดคล้องกันทำให้ confidence เพิ่มขึ้นว่า failure mode นี้เป็นปัญหาเชิงระบบ ไม่ใช่ artifact ของซิม 2D เท่านั้น

## 9. ข้อจำกัดของงานปัจจุบัน

1. แบบจำลองยังเป็นแขนสองข้อต่อหลัก ไม่ใช่ biomechanical arm ที่ครบทุก degree-of-freedom
2. ยังไม่มี muscle model หรือ fatigue model
3. ยังไม่มี sensor noise, calibration drift, backlash, compliance หรือ mechanical play
4. ยังไม่มี contact ระหว่างโครง exoskeleton กับผิว/สายรัดของมนุษย์
5. felt payload estimate ยังเป็นค่าประมาณจาก peak torque ไม่ใช่ผลจากมนุษย์จริง
6. controller ยังเป็นแบบง่าย ไม่ใช่ impedance/admittance control ที่เหมาะกับ human-robot interaction จริง
7. torque limit ใน simulation เป็นค่าตั้งต้นเพื่อทดลอง ไม่ใช่สเปกมอเตอร์ที่เลือกแล้ว
8. 3D model ยังจำกัดการเคลื่อนไหวในระนาบยกของเป็นหลัก

## 10. ข้อเสนอสำหรับการพัฒนาต่อ

### 10.1 เพิ่ม sensor model ให้สมจริงขึ้น

ควรเพิ่ม:

- sensor noise
- delay แบบแยก sensor delay และ motor delay
- low-pass filter
- calibration offset
- saturation ของ sensor
- sensor ที่วัด interaction force ที่สายรัดแทน joint torque ตรง ๆ

### 10.2 เพิ่ม controller ด้านความปลอดภัย

ควรทดลอง:

- torque ramp limit
- rate limit ของ motor torque
- impedance control
- assist-as-needed
- cutoff เมื่อ error สูงเกิน threshold
- watchdog ถ้า sensor signal ผิดปกติ

### 10.3 เพิ่มการเลือกมอเตอร์

จากผลปัจจุบัน มอเตอร์หัวไหล่ในสถานการณ์ feedback สามารถชน 80 Nm ได้ จึงควรศึกษา:

- continuous torque
- peak torque
- gear ratio
- backdrivability
- thermal limit
- response time
- motor + gearbox inertia

### 10.4 เพิ่มโมเดล 3D ที่ใกล้ฮาร์ดแวร์ขึ้น

ควรเพิ่ม:

- โครง exoskeleton ที่มี joint alignment error
- จุดยึดกับแขน
- link mass ของโครงช่วยแรง
- shoulder abduction/adduction
- wrist/hand payload grip
- contact constraints ระหว่างมือกับวัตถุ

### 10.5 สร้าง experiment package สำหรับรายงานรอบถัดไป

ควรมีชุดทดลองมาตรฐาน:

```text
baseline: no assist
ideal assist: human_only sensor
bad sensor: combined sensor
noisy sensor
delayed sensor
torque-limited motor
rate-limited motor
```

จากนั้นสรุป metrics:

- peak human torque reduction
- motor saturation fraction
- tracking error
- energy/work
- stability score

## 11. สรุป

โครงการนี้เริ่มสร้างฐาน simulation สำหรับแขน exoskeleton ช่วยยกของ โดยตั้งเป้าหมายแรกให้ระบบช่วยลดภาระครึ่งหนึ่ง ทำให้ของ 5 kg รู้สึกใกล้เคียง 2.5 kg ผลการทดลองใน 2D และ 3D แสดงว่าแนวคิด force amplification แบบ `gain = 1.0` สามารถทำตามเป้าหมายได้ภายใต้สมมติฐานว่า sensor อ่านแรงจากมนุษย์ได้อย่างถูกต้อง

อย่างไรก็ตาม การทดลอง sensor feedback แสดงความเสี่ยงสำคัญ: ถ้า sensor อ่านแรงรวมที่มีแรงมอเตอร์ปนอยู่ ระบบจะเกิด positive feedback จนมอเตอร์ชน torque limit และ tracking error เพิ่มขึ้นมาก ผลนี้เป็นข้อค้นพบหลักของระยะปัจจุบัน และควรถูกใช้เป็นโจทย์ออกแบบสำคัญก่อนสร้าง hardware จริง

ดังนั้นข้อสรุปของระยะนี้คือ:

```text
แนวคิดช่วยแรงแบบมนุษย์ออกเท่าไร มอเตอร์ช่วยเท่านั้น ใช้ได้ใน simulation
แต่ต้องมี sensor/control architecture ที่แยกแรงมนุษย์ออกจากแรงมอเตอร์ได้
มิฉะนั้นระบบมีความเสี่ยงต่อ positive feedback และ actuator saturation
```

## 12. เอกสารอ้างอิง

1. MuJoCo official site: https://mujoco.org/
2. MuJoCo Python documentation: https://mujoco.readthedocs.io/en/stable/python.html
3. MuJoCo XML reference: https://mujoco.readthedocs.io/en/stable/XMLreference.html
4. MuJoCo computation and actuator model: https://mujoco.readthedocs.io/en/stable/computation/index.html
5. Local source: `exosim/arm.py`
6. Local source: `exosim/scenario.py`
7. Local source: `exosim/mujoco_simulate.py`
8. Local model: `models/arm_exoskeleton_3d.xml`
9. Local results: `outputs/sensor_feedback_summary.csv`
10. Local results: `outputs/sensor_feedback_3d_summary.csv`
