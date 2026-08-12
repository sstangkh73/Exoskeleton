# Product Engineering Blueprint v0.1: Arm Exoskeleton ช่วยยกของ

วันที่: 3 กรกฎาคม 2026  
สถานะ: concept engineering blueprint สำหรับ simulation และ bench prototype  
ภาพ blueprint: `outputs/exo_product_blueprint_v0_1.svg`  
ภาพ preview PNG: `outputs/exo_product_blueprint_v0_1.png`  
config: `design/product_architecture_v0_1.json`

## 1. คำเตือนสถานะ

เอกสารนี้เป็น blueprint ระดับหลักการวิศวกรรม ไม่ใช่แบบผลิตจริง ไม่ใช่แบบผ่าน safety certification และยังไม่ควรนำไปให้มนุษย์ใส่จริงโดยตรง สิ่งที่ทำได้ตอนนี้คือใช้เป็นฐานสำหรับ CAD, simulation, dummy-arm bench test และการเลือก component เบื้องต้น

## 2. Product goal

เป้าหมายของ product v0.1:

```text
ยก payload 5 kg ให้ผู้ใช้รู้สึกใกล้เคียง 2.5 kg
โดยใช้ force amplification gain = 1.0
และต้องวัด human-only effort ไม่ใช่แรงรวมคน+มอเตอร์
```

จากซิมก่อนหน้า หาก sensor อ่านแรงคนอย่างเดียว ระบบแบ่งแรงบิดได้ประมาณ 50/50 แต่หาก sensor อ่านแรงรวมคน+มอเตอร์ ระบบเกิด positive feedback และ motor saturation

## 3. Architecture รวม

ระบบแบ่งเป็น 5 ส่วน:

1. โครงกลไกด้านข้างแขน
2. ชุดมอเตอร์และ transmission ที่ shoulder/elbow
3. cuff/strap สำหรับส่งแรงเข้าร่างกาย
4. sensor และ controller
5. battery, motor driver, wiring และ safety loop

ภาพรวม:

```text
24 V battery
  -> main fuse
  -> emergency stop
  -> motor drivers
  -> shoulder/elbow motors

load cells / series elastic sensors
  -> controller
  -> human-only effort estimator
  -> torque command
  -> motor drivers
```

## 4. โครงกลไกและขนาดหลัก

| ส่วน | ค่าออกแบบ v0.1 |
|---|---:|
| upper arm link nominal | 310 mm |
| upper arm adjustment | 260-360 mm |
| forearm link nominal | 340 mm |
| forearm adjustment | 280-380 mm |
| lateral offset ของ exo จากแขน | 55 mm |
| cuff width nominal | 80 mm |
| padding thickness | 8-15 mm |

เหตุผลที่ใช้โครงด้านข้างแขน:

- เห็น alignment ของ shoulder/elbow ได้ชัด
- วาง cuff และ sensor ได้ง่าย
- ทำ prototype ง่ายกว่าโครงรอบแขนเต็มวง
- เหมาะกับการเริ่มจาก elbow module

ข้อเสีย:

- ต้องระวังแรงบิดด้านข้าง
- ต้องมี cuff อย่างน้อยสองจุดต่อ segment
- ต้องปรับ alignment ให้ตรงกับข้อศอกจริง

## 5. Joint design

### 5.1 Shoulder joint

| รายการ | ค่า |
|---|---:|
| DOF | shoulder flexion/extension |
| active range | -20 ถึง 110 deg |
| mechanical hard stop | -35 ถึง 125 deg |
| motor placement | torso/backpack side plate |
| transmission | timing belt หรือ cable/capstan |
| initial ratio | 50:1 |

หลักการวางมอเตอร์ shoulder: ไม่ควรเอามอเตอร์หนักไปอยู่บนต้นแขน เพราะจะเพิ่ม inertia ของแขนทั้งระบบ ควรวางบน torso/backpack แล้วส่งแรงด้วย belt/cable ไปยัง shoulder pulley

### 5.2 Elbow joint

| รายการ | ค่า |
|---|---:|
| DOF | elbow flexion/extension |
| active range | 0 ถึง 135 deg |
| mechanical hard stop | 0 ถึง 145 deg |
| motor placement | distal upper arm ใกล้ข้อศอก |
| transmission | compact belt/gear stage |
| initial ratio | 40:1 |

Elbow เป็น module ที่ควรสร้างก่อน shoulder เพราะ axis ง่ายกว่า ทดสอบง่ายกว่า และความเสี่ยง biomechanical ต่ำกว่า shoulder

## 6. Motor and transmission targets

### 6.1 Shoulder actuator

| รายการ | ค่า |
|---|---:|
| design peak joint torque | 35 Nm |
| continuous joint torque target | 15 Nm |
| early human-test software cap | 20 Nm |
| sim stress-test limit | 80 Nm |
| driver voltage | 24 V |
| peak current target | 12 A |
| continuous current target | 5 A |
| transmission ratio เริ่มต้น | 50:1 |
| encoder | 12-14 bit minimum |

หมายเหตุ: ค่า 80 Nm เป็น stress-test limit ในซิม ไม่ใช่ค่าที่ควรปล่อยให้ระบบจริงใช้กับมนุษย์

### 6.2 Elbow actuator

| รายการ | ค่า |
|---|---:|
| design peak joint torque | 15 Nm |
| continuous joint torque target | 5 Nm |
| early human-test software cap | 8 Nm |
| sim stress-test limit | 60 Nm |
| driver voltage | 24 V |
| peak current target | 8 A |
| continuous current target | 3 A |
| transmission ratio เริ่มต้น | 40:1 |
| encoder | 12-14 bit minimum |

## 7. Power system

Power architecture v0.1:

| ส่วน | ค่า |
|---|---:|
| battery nominal voltage | 24 V |
| capacity | 6 Ah |
| energy | 144 Wh |
| BMS peak current | 20 A |
| main fuse | 15 A |
| shoulder driver branch fuse | 10 A |
| elbow driver branch fuse | 7.5 A |
| logic DC/DC fuse | 2 A |
| logic 5 V rail | 3 A |
| logic 3.3 V rail | 1 A |

Emergency stop ควรตัดอย่างน้อย driver enable loop และควรมีทางตัด main power ใน bench test ด้วย

## 8. Wiring

| เส้นทาง | สายเริ่มต้น |
|---|---|
| main 24 V battery bus | AWG16 หรือเทียบเท่า |
| motor power / phase leads | AWG18 ระยะสั้น |
| logic power | AWG22 |
| sensor signal | AWG24 shielded/twisted pair |
| communication | CAN หรือ RS485 twisted pair |

Routing rules:

- แยกสาย power ออกจากสาย sensor ให้มากที่สุด
- มี strain relief ทุกจุดที่ขยับ
- มี service loop ที่ shoulder และ elbow
- ใส่ fuse ใกล้ battery มากที่สุด
- ห้ามลากสายตึงผ่านข้อพับ elbow
- sensor/load-cell wire ควร shield หรือ twisted pair

## 9. Sensor architecture

ระบบ force amplification ต้องรู้แรงที่มนุษย์ตั้งใจออก ไม่ใช่แรงรวมของมนุษย์กับมอเตอร์

Sensor ที่ควรพิจารณา:

- load cell ระหว่าง cuff กับ exo link
- series elastic element แล้ววัด deflection
- joint torque sensor พร้อม motor torque observer subtraction
- force sensor ที่ handle หรือ forearm interface

Sensor ที่ไม่ควรใช้เดี่ยว ๆ:

- motor current sensor เป็น human effort sensor หลัก
- sensor ที่อ่านแรงรวมคน+มอเตอร์แล้วป้อนเข้าตัวคูณ gain ตรง ๆ

## 10. Control and safety

Control loop target:

```text
200-500 Hz สำหรับ prototype แรก
```

Safety features ก่อนทดลองกับคน:

- mechanical hard stops
- software torque limit
- torque rate limit
- emergency stop
- watchdog ถ้า sensor disagree
- motor driver fault handling
- encoder sanity check
- dummy-arm bench test
- no-payload test
- low-payload test 0.5-1 kg

## 11. Force path

### Elbow assist

```text
elbow motor
  -> belt/gear
  -> elbow output pulley
  -> forearm exo link
  -> forearm cuff
  -> user's forearm and payload

reaction torque
  -> upper arm link
  -> upper arm cuffs
  -> user's upper arm / torso
```

### Shoulder assist

```text
shoulder motor on torso
  -> cable/belt
  -> shoulder pulley
  -> upper arm exo link
  -> upper arm cuffs

reaction torque
  -> torso backpack plate
  -> chest/shoulder straps
```

## 12. Product build order

1. Elbow-only bench rig
2. Dummy arm with load cell and series elastic sensor
3. Elbow wearable prototype with low torque cap
4. Shoulder transmission bench test
5. Full single-arm prototype with payload below 1 kg
6. Incremental payload increase only after safety review

## 13. Open engineering questions

- ใช้ load cell ที่ cuff หรือ series elastic ที่ transmission ดีกว่า
- shoulder cable routing จะเสียดสีกับลำตัวหรือไม่
- cuff กว้าง 80 mm พอรับแรงโดยไม่เจ็บหรือไม่
- motor/gearbox backlash ทำให้ force amplification สั่นหรือไม่
- torque rate limit ควรตั้งเท่าไร
- battery 24 V เพียงพอหรือควรขยับไป 36 V ใน prototype ต่อไป
- ควรทำ elbow-only product ก่อนหรือทำ shoulder+elbow พร้อมกัน

## 14. Files

```text
outputs/exo_product_blueprint_v0_1.svg
outputs/exo_product_blueprint_v0_1.png
design/product_architecture_v0_1.json
docs/product_engineering_blueprint_v0_1.th.md
docs/mechanical_design_v0_1.th.md
models/arm_exoskeleton_design_v0_1.xml
```

## 15. References

1. NASA Human Integration Design Handbook: https://www.nasa.gov/wp-content/uploads/2015/03/human_integration_design_handbook_revision_1.pdf
2. NASA physical characteristics and capabilities dataset handbook: https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-hb-004-rev-a-dec2023.pdf
3. MuJoCo official site: https://mujoco.org/
4. MuJoCo XML reference: https://mujoco.readthedocs.io/en/stable/XMLreference.html
5. OpenSim upper extremity model overview: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim24/pages/54002482/Upper%2BExtremity%2BModel
