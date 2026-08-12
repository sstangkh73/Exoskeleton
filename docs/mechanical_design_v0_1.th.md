# Mechanical Design Spec v0.1: แขน Exoskeleton ช่วยยกของ

วันที่: 3 กรกฎาคม 2026  
สถานะ: แนวคิดเชิงวิศวกรรมสำหรับ simulation/CAD ยังไม่พร้อมให้มนุษย์ใส่จริง  
ไฟล์ config คู่กัน: `design/exo_mechanical_design_v0_1.json`  
โมเดล 3D คู่กัน: `models/arm_exoskeleton_design_v0_1.xml`

## 1. เป้าหมายของ design v0.1

เป้าหมายแรกของ exoskeleton คือช่วยให้การยกของ 5 kg รู้สึกใกล้เคียงกับ 2.5 kg โดยไม่ต้องทำให้ระบบฉลาดเกินไปตั้งแต่ต้น วิธีควบคุมพื้นฐานคือ force amplification:

```text
motor torque = gain * measured human torque
gain = 1.0 -> มอเตอร์ช่วยแรงบิดเท่ากับแรงบิดจากมนุษย์
```

จากผลซิมก่อนหน้า โหมด `human_only` ทำเป้าหมายนี้ได้ใน simulation แต่โหมด `combined` ซึ่ง sensor อ่านแรงคนรวมกับแรงมอเตอร์ ทำให้ motor saturation และ tracking error สูงขึ้นมาก ดังนั้น design v0.1 ต้องถือว่า “sensor architecture” สำคัญพอ ๆ กับมอเตอร์

## 2. หลักการออกแบบ

1. เริ่มจากแขนขวา 1 ข้างก่อน
2. จำกัดการช่วยแรงในระนาบยกของ หรือ sagittal plane ก่อน
3. Active DOF แรกคือ elbow flexion/extension และ shoulder flexion/extension
4. วางมอเตอร์หนักไว้ใกล้ลำตัวหรือใกล้ต้นแขน ไม่วางไว้ปลายแขน
5. จุดหมุนของ exo ต้องใกล้กับ joint axis ของมนุษย์มากที่สุด
6. จุดยึดต้องกระจายแรงผ่าน cuff กว้าง ไม่กดเป็นจุด
7. ต้องมี mechanical hard stop และ software torque limit ก่อนทดลองกับคน
8. ห้ามใช้ sensor ที่อ่านแรงรวมคน+มอเตอร์เป็นแหล่งสั่ง force amplification โดยตรง

## 3. ข้อมูลร่างกายตั้งต้น

ค่าตั้งต้นใน simulation ปัจจุบัน:

| รายการ | ค่า nominal |
|---|---:|
| ความยาวต้นแขน | 0.31 m |
| ความยาวปลายแขน | 0.34 m |
| มวลต้นแขนในซิม | 2.1 kg |
| มวลปลายแขนในซิม | 1.65 kg |
| payload เป้าหมาย | 5.0 kg |

ช่วงปรับที่ควรออกแบบใน CAD:

| ส่วน | ช่วงปรับ |
|---|---:|
| upper arm link | 0.26-0.36 m |
| forearm link | 0.28-0.38 m |

หมายเหตุสำคัญ: ข้อมูล anthropometry ต้องวัดจากผู้ใช้จริงก่อนล็อก CAD โดยเฉพาะความยาวแขนรวมและตำแหน่ง elbow/shoulder axis ไม่ควรเอาค่าร้อยละของแต่ละ segment มาบวกกันแล้วถือว่าเป็นคนคนเดียวกัน เพราะสัดส่วนร่างกายแต่ละส่วนไม่ได้แปรไปพร้อมกันเสมอ

## 4. Architecture ที่เลือก

### 4.1 ภาพรวม

Design v0.1 เป็น single-arm exoskeleton แบบ lateral frame:

```text
torso harness / backpack plate
  -> shoulder assist pulley or belt stage
  -> upper-arm lateral link
  -> elbow actuator near distal upper arm
  -> forearm lateral link
  -> forearm cuff / hand-side load path
```

แรงจาก payload ผ่านมือและปลายแขนเข้าสู่ร่างกายมนุษย์ ขณะเดียวกัน exo สร้างแรงบิดช่วยที่ shoulder/elbow แล้วส่งแรงย้อนกลับเข้าที่ cuff และ torso harness

### 4.2 เหตุผลที่ใช้ lateral frame

- เข้าถึง joint axis ของ elbow ได้ง่าย
- วาง link นอกแขน ลดการชนกับลำตัว
- เห็นและตรวจ alignment ง่ายใน CAD/sim
- เพิ่ม cuff หรือ sensor ระหว่าง link กับแขนได้
- เหมาะกับ prototype ที่ยังไม่ต้องสวยหรือบาง

ข้อเสียคืออาจมี moment ด้านข้างและต้องระวังการบิดแขน จึงควรมี cuff อย่างน้อยสองตำแหน่งต่อ segment เพื่อกระจายแรงและลดการหมุนหลวม

## 5. Degree of Freedom และมุมการหมุน

### 5.1 Shoulder flexion/extension

ใน v0.1 ช่วยเฉพาะ shoulder flexion/extension ในระนาบยกของ:

| รายการ | ค่า |
|---|---:|
| ช่วงใช้งานที่อนุญาตใน controller | -20 ถึง 110 deg |
| hard stop เชิงกล | -35 ถึง 125 deg |
| axis ในซิม | `0 -1 0` |
| ตำแหน่ง motor ที่แนะนำ | torso/backpack side plate |
| transmission | cable หรือ timing belt ไปยัง pulley ที่ shoulder |

เหตุผลที่ไม่ควรวาง shoulder motor ไว้บนต้นแขนโดยตรง: เพิ่ม inertia ให้แขน และทำให้ผู้ใช้ต้องแบกน้ำหนักของ actuator ในทุกการเคลื่อนไหว

ข้อควรระวัง: shoulder จริงไม่ใช่ hinge ธรรมดา จุดหมุนของ shoulder complex เคลื่อนตาม scapula และท่าทางลำตัว ดังนั้น shoulder assist ใน prototype แรกควรเริ่มจาก bench test หรือ dummy arm ก่อน ไม่ควรใส่กับคนทันที

### 5.2 Elbow flexion/extension

Elbow เป็น DOF ที่เหมาะสำหรับ build hardware ก่อน shoulder:

| รายการ | ค่า |
|---|---:|
| ช่วงใช้งานที่อนุญาตใน controller | 0 ถึง 135 deg |
| hard stop เชิงกล | 0 ถึง 145 deg |
| axis ในซิม | `0 -1 0` |
| ตำแหน่ง motor ที่แนะนำ | ด้านข้างต้นแขน ใกล้ข้อศอก |
| transmission | coaxial belt/gear stage ที่ elbow joint |

ข้อดีของการวาง elbow motor ที่ต้นแขนใกล้ข้อศอก:

- ไม่เพิ่มน้ำหนักที่ปลายแขนมากเกินไป
- torque path สั้นกว่า remote cable ยาว
- align กับ elbow hinge ได้ง่ายกว่า shoulder
- เหมาะกับการสร้าง prototype แรก

## 6. การวางมอเตอร์และส่งแรง

### 6.1 Shoulder actuator

ตำแหน่งที่เลือก:

```text
torso/backpack plate -> cable/belt -> shoulder pulley -> upper arm link
```

เหตุผล:

- มอเตอร์หนักอยู่กับ torso ไม่อยู่บนแขน
- reaction torque ส่งกลับเข้าลำตัว ไม่ดึงแขนผิดทิศมากเกินไป
- maintenance ง่ายกว่า motor ฝังที่ shoulder joint

แนวทางส่งแรง:

1. ใช้ timing belt หรือ cable/capstan
2. มี pulley ที่ใกล้ shoulder axis
3. มี idler/tensioner ปรับความตึง
4. เพิ่ม series elastic element หรือ torque sensor ในรุ่นถัดไป

ค่าตั้งต้น:

| รายการ | ค่า |
|---|---:|
| design peak joint torque target | 35 Nm |
| continuous torque target | 15 Nm |
| software limit สำหรับ human-safe early test | 20 Nm |
| simulation stress-test limit เดิม | 80 Nm |

### 6.2 Elbow actuator

ตำแหน่งที่เลือก:

```text
distal upper arm motor housing -> belt/gear -> elbow joint pulley -> forearm link
```

เหตุผล:

- ลดน้ำหนักที่ forearm
- โครงสร้างสั้นและแข็งกว่า cable ยาว
- วัดแรงระหว่าง cuff/link ได้ง่ายกว่า

ค่าตั้งต้น:

| รายการ | ค่า |
|---|---:|
| design peak joint torque target | 15 Nm |
| continuous torque target | 5 Nm |
| software limit สำหรับ human-safe early test | 8 Nm |
| simulation stress-test limit เดิม | 60 Nm |

## 7. Force path

### 7.1 ตอนช่วย elbow

เมื่อต้องช่วยงอหรือพยุง elbow:

```text
motor torque ที่ elbow
  -> elbow pulley/gear
  -> forearm exo link
  -> forearm cuff
  -> ปลายแขน/มือ/payload

reaction torque
  -> upper arm link
  -> upper arm cuff
  -> ต้นแขน/torso
```

แรงที่ผู้ใช้รู้สึกไม่ได้หายไป แต่ถูกย้ายบางส่วนไปที่ cuff และโครง exo ดังนั้น cuff ต้องกว้างพอและไม่กดเส้นประสาท/ข้อพับ

### 7.2 ตอนช่วย shoulder

เมื่อต้องช่วยยกแขน:

```text
shoulder motor ที่ torso
  -> belt/cable
  -> shoulder pulley
  -> upper arm link
  -> upper arm cuff/forearm link

reaction torque
  -> torso harness/backpack plate
  -> ลำตัว
```

จุดยากคือ shoulder axis ของมนุษย์ไม่อยู่นิ่ง จึงควรให้ shoulder module มี compliance หรือ alignment adjustment

## 8. การใส่กับแขนและจุดยึด

### 8.1 Torso harness

หน้าที่:

- รับ reaction torque จาก shoulder actuator
- เป็นฐานของ motor/แบตเตอรี่/อิเล็กทรอนิกส์
- ลดน้ำหนักที่แขน

ข้อกำหนด:

- มี shoulder strap และ chest strap
- หลีกเลี่ยงการกดคอ/รักแร้
- ต้องไม่จำกัดการหายใจ
- ถอดออกได้เร็ว

### 8.2 Upper arm cuffs

ตำแหน่งตั้งต้นจาก shoulder:

| cuff | ตำแหน่ง |
|---|---:|
| proximal upper cuff | 0.11 m |
| distal upper cuff | 0.24 m |

ข้อกำหนด:

- กว้างอย่างน้อย 60 mm
- มี padding 8-15 mm
- ไม่ทับ elbow crease
- ไม่กด medial elbow/ulnar nerve
- ต้องปรับเส้นรอบวงได้

### 8.3 Forearm cuffs

ตำแหน่งตั้งต้นจาก elbow:

| cuff | ตำแหน่ง |
|---|---:|
| proximal forearm cuff | 0.10 m |
| distal forearm cuff | 0.25 m |

ข้อกำหนด:

- ไม่ทับ wrist joint line
- ไม่ขัด pronation/supination มากเกินไป
- ควรกระจายแรงบน dorsal/lateral forearm
- หลีกเลี่ยงแรงกดเป็นจุด

## 9. ขนาด น้ำหนัก และ mass budget

เป้าหมาย mass budget:

| ส่วน | เป้าหมาย |
|---|---:|
| มวลรวม wearable | ไม่เกิน 3.0 kg |
| torso/backpack module | ไม่เกิน 1.1 kg |
| upper-arm mounted module | ไม่เกิน 0.9 kg |
| forearm mounted module | ไม่เกิน 0.35 kg |
| distal forearm preferred max | ไม่เกิน 0.25 kg |

หลักการคือย้ายของหนักเข้าหาลำตัวหรืออย่างน้อยเข้าหา elbow/upper arm เพราะมวลที่ปลายแขนเพิ่ม moment of inertia และทำให้ผู้ใช้รู้สึกหนักขึ้น แม้มอเตอร์ช่วยแรงโน้มถ่วงได้บางส่วนก็ตาม

## 10. Sensor architecture

### 10.1 Sensor ที่ต้องการ

ระบบ force amplification ต้องประมาณ “แรงที่มนุษย์ตั้งใจออก” โดยไม่เอาแรงมอเตอร์กลับมาขยายซ้ำ วิธีที่เป็นไปได้:

- load cell ระหว่าง cuff กับ exo link
- series elastic actuator วัด deflection ของ spring
- joint torque sensor แล้วใช้ motor torque observer ลบแรงมอเตอร์ออก
- force sensor ที่ handle หรือ forearm interface

### 10.2 Sensor ที่ไม่ควรใช้เดี่ยว ๆ

ไม่ควรใช้ motor current sensor เป็น human effort sensor เพียงตัวเดียว เพราะกระแสมอเตอร์บอกแรงมอเตอร์ ไม่ได้แยกเจตนาของมนุษย์โดยตรง

### 10.3 บทเรียนจากซิม

ผลซิม `combined` แสดงชัดว่า sensor ที่อ่านแรงรวมคน+มอเตอร์ทำให้เกิด positive feedback:

```text
combined sensor -> measured torque สูงเกินจริง -> motor torque สูงขึ้น -> measured torque สูงขึ้นอีก
```

ดังนั้น design v0.1 ต้องมี experiment ตรวจ sensor separation ก่อนใส่กับคน

## 11. ขีดจำกัดความปลอดภัย

ก่อนทดลองกับมนุษย์ต้องมีอย่างน้อย:

- mechanical hard stop ที่ shoulder และ elbow
- software torque limit ต่ำกว่าค่า stress-test
- torque rate limit
- emergency stop
- watchdog ถ้า sensor ผิดปกติ
- test กับ dummy arm
- test แบบไม่มี payload
- test แบบ payload เบา เช่น 0.5-1 kg

ค่าควบคุมเริ่มต้นสำหรับ human-safe early test ยังไม่ใช่ค่าที่อนุมัติทางความปลอดภัย แต่เป็นเพดานอนุรักษ์นิยมสำหรับ simulation/bench planning:

| joint | initial software limit |
|---|---:|
| shoulder | 20 Nm |
| elbow | 8 Nm |

## 12. Build order ที่แนะนำ

### Phase A: Elbow-only bench rig

สร้าง elbow module ก่อน:

- upper arm dummy link
- forearm dummy link
- elbow hinge
- elbow actuator
- forearm cuff/load interface
- load cell หรือ spring deflection sensor

เป้าหมายคือพิสูจน์ว่า force amplification แบบ `human_only` ไม่ feedback

### Phase B: Wearable elbow prototype

เพิ่ม cuff จริงและ strap:

- ยังไม่เปิด shoulder motor
- payload ต่ำ
- torque limit ต่ำ
- ทดสอบกับ dummy ก่อนคน

### Phase C: Shoulder assist simulation-to-hardware

เพิ่ม shoulder module:

- motor อยู่ torso/backpack
- ส่งแรงด้วย cable/belt
- hard stop และ compliance
- ตรวจ alignment ของ shoulder อย่างเข้มงวด

### Phase D: Integrated single-arm lifting assist

รวม elbow + shoulder:

- sensor fusion
- torque rate limit
- emergency stop
- payload 5 kg หลังผ่าน test ลำดับก่อนหน้า

## 13. สิ่งที่อัปเดตใน MuJoCo design model

โมเดล `models/arm_exoskeleton_design_v0_1.xml` เพิ่มองค์ประกอบแทนตำแหน่งเชิงภาพและเชิงกล:

- torso backpack plate
- shoulder motor housing
- shoulder transmission cable
- upper arm cuffs 2 จุด
- elbow motor housing บน distal upper arm
- elbow pulley/drive plate
- forearm cuffs 2 จุด
- forearm link และ handle-side bracket

โมเดลนี้ยังไม่ใช่ CAD จริง แต่ช่วยให้ซิมเห็นมวลและตำแหน่งของอุปกรณ์มากกว่าโมเดล minimal เดิม

## 14. คำสั่งที่เกี่ยวข้อง

Render preview:

```powershell
.\.venv\Scripts\python.exe -m exosim.render_mujoco_preview --model models\arm_exoskeleton_design_v0_1.xml --output outputs\arm_3d_design_v0_1_preview.png
```

Run 3D simulation:

```powershell
.\.venv\Scripts\python.exe -m exosim.mujoco_simulate --model models\arm_exoskeleton_design_v0_1.xml --control-mode force_amp --payload-kg 5 --felt-payload-kg 2.5 --output outputs\lift_3d_design_v0_1_force_amp.csv
```

## 15. ผลตรวจเบื้องต้นใน MuJoCo

หลังเพิ่มมวลและ geometry ของ cuff/motor/link เข้าโมเดล design v0.1 แล้วรัน force amplification แบบ `human_only`:

```text
peak human shoulder = 23.69 Nm
peak motor shoulder = 23.68 Nm
felt payload by shoulder peak = 2.50 kg
shoulder motor saturation = 0.00%
shoulder max tracking error = 17.97 deg
```

ผลนี้แปลว่า force split ยังทำงานตามแนวคิด 50/50 แต่ controller เดิมเริ่มตาม trajectory ได้แย่ลงเพราะโมเดลหนักและซับซ้อนขึ้น ดังนั้นรอบถัดไปต้อง tune controller และอาจเพิ่ม feedforward dynamics สำหรับมวล exo จริง

เมื่อรัน bad-sensor mode แบบ `combined` กับโมเดลเดียวกัน:

```text
peak measured shoulder = 117.07 Nm
peak motor shoulder = 80.00 Nm
shoulder motor saturation = 44.93%
shoulder max tracking error = 20.25 deg
```

ผลนี้ยืนยันว่า mechanical layout ใหม่ไม่ได้แก้ positive feedback เอง ถ้า sensor อ่านแรงรวมคน+มอเตอร์ ระบบยังชน motor limit เหมือนเดิม

ไฟล์ผลลัพธ์:

```text
outputs/lift_3d_design_v0_1_force_amp.csv
outputs/lift_3d_design_v0_1_bad_sensor.csv
outputs/arm_3d_design_v0_1_preview.png
```

## 16. สรุป design decision

Design v0.1 เลือกแนวทาง conservative:

```text
โครงด้านข้างแขน
มอเตอร์ shoulder อยู่ torso/backpack
มอเตอร์ elbow อยู่ใกล้ข้อศอกบนต้นแขน
ไม่วางมอเตอร์หนักที่ปลายแขน
ใช้ cuff กว้างสองจุดต่อ segment
เริ่ม build จาก elbow module ก่อน
ห้ามใช้ sensor ที่อ่านแรงรวมคน+มอเตอร์เป็น feedback ตรง ๆ
```

การออกแบบนี้ยังไม่ใช่แบบพร้อมผลิต แต่เป็น baseline ที่ดีสำหรับ CAD, simulation และ bench prototype รอบต่อไป

## 17. แหล่งอ้างอิง

1. NASA Human Integration Design Handbook, NASA/SP-2010-3407 Revision 1: https://www.nasa.gov/wp-content/uploads/2015/03/human_integration_design_handbook_revision_1.pdf
2. NASA OCHMO-HB-004 Revision A, Physical Characteristics and Capabilities Data Sets: https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-hb-004-rev-a-dec2023.pdf
3. MuJoCo official site: https://mujoco.org/
4. MuJoCo Python documentation: https://mujoco.readthedocs.io/en/stable/python.html
5. MuJoCo XML reference: https://mujoco.readthedocs.io/en/stable/XMLreference.html
6. OpenSim Upper Extremity Model overview: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim24/pages/54002482/Upper%2BExtremity%2BModel
7. de Leva, P. 1996, Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters: https://pubmed.ncbi.nlm.nih.gov/8872282/
