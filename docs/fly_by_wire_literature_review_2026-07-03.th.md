# Fly-by-Wire Literature Review สำหรับ Arm Exoskeleton

วันที่: 3 กรกฎาคม 2026  
เป้าหมาย: หาแนวคิดจาก fly-by-wire มาปรับใช้กับระบบ exoskeleton ช่วยแรงแบบ force amplification  
สถานะ: literature note สำหรับออกแบบ architecture รอบต่อไป ไม่ใช่ข้อสรุปด้านความปลอดภัย

## 1. ทำไม fly-by-wire เกี่ยวกับ exoskeleton

Fly-by-wire ไม่ใช่แค่ “ใช้สายไฟแทนสายกลไก” แต่เป็น architecture ที่ให้คอมพิวเตอร์อยู่ตรงกลางระหว่างมนุษย์กับ actuator:

```text
pilot input / inceptor
  -> sensor
  -> flight control computer
  -> control law + envelope protection
  -> actuator command
  -> aircraft surface
```

สำหรับแขน exoskeleton ของเรา สามารถแปลงเป็น:

```text
human effort / cuff force / joint motion
  -> human-only intent estimator
  -> assist control law + safety envelope
  -> motor torque command
  -> shoulder/elbow actuator
  -> arm + payload
```

สิ่งที่น่าสนใจที่สุดไม่ใช่การ copy control law ของเครื่องบิน แต่คือแนวคิด:

- แยก intent ของมนุษย์ออกจาก actuator feedback
- มี safety envelope ที่ controller ห้ามข้าม
- มี degraded mode เมื่อ sensor/actuator ไม่น่าเชื่อถือ
- มี haptic cue หรือ force cue แจ้งผู้ใช้เมื่อใกล้ limit
- ทดสอบกับ iron bird / hardware-in-the-loop ก่อนใช้จริง

## 2. Reading priority

### อันดับ 1: NASA F-8 Digital Fly-By-Wire papers

ควรอ่านก่อน เพราะเป็นต้นแบบเชิงระบบของ digital fly-by-wire ที่มีทั้ง hardware, software, backup, simulator และ flight test

1. **Design and Development Experience With a Digital Fly-By-Wire Flight Control System**
   - แหล่ง: NASA NTRS
   - ลิงก์: https://ntrs.nasa.gov/api/citations/19760024053/downloads/19760024053.pdf
   - ประเด็นหลัก: digital primary control, analog backup, iron bird simulator, data acquisition, hardware/software integration
   - เอามาใช้กับเรา:
     - สร้าง `arm iron bird`: dummy arm + motor + sensor + controller
     - แยก primary controller กับ fallback mode
     - มี telemetry ของ internal controller state ไม่ใช่ดูแค่มุม/torque ปลายทาง

2. **Flight Test Experience With the F-8 Digital Fly-By-Wire System**
   - ผู้เขียน: Kenneth J. Szalai
   - แหล่ง: NASA Flight Research Center
   - ลิงก์: https://ntrs.nasa.gov/api/citations/19760024056/downloads/19760024056.pdf
   - ประเด็นหลัก: performance, handling qualities, software management, preflight testing, engineering interfaces
   - เอามาใช้กับเรา:
     - ต้องมี pre-run checklist สำหรับ exo ก่อนเปิด motor
     - ต้องมี monitor/debug display ของ controller
     - ใช้ staged testing: simulation -> bench -> dummy arm -> low payload

### อันดับ 2: FBW manual control และ control law design

3. **Fly-by-Wire Augmented Manual Control - Basic Design Considerations**
   - แหล่ง: ICAS 2012
   - ลิงก์: https://www.icas.org/icas_archive/ICAS2012/PAPERS/605.PDF
   - ประเด็นหลัก: augmented manual control, neutral behavior, response type, integral path, pilot workload
   - เอามาใช้กับเรา:
     - ต้องนิยามว่าเมื่อผู้ใช้ “หยุดออกแรง” exo จะทำอะไร
       - ค้างตำแหน่ง?
       - ค่อย ๆ ปล่อย?
       - ช่วยพยุง gravity ต่อ?
       - กลับสู่ zero torque?
     - นี่สำคัญกับ force amplification มาก เพราะ neutral behavior ผิดอาจทำให้แขนถูกดึง/ค้างโดยไม่ตั้งใจ

4. **The Development of a Civilian Fly By Wire Flight Control System**
   - ผู้เขียน: E. Kleemann, D. Dey, R. Recksiek
   - แหล่ง: ICAS 2000
   - ลิงก์: https://www.icas.org/icas_archive/ICAS2000/PAPERS/ICA0643.PDF
   - ประเด็นหลัก: operational FBW, safety, envelope protection, common handling qualities, active load control
   - เอามาใช้กับเรา:
     - ออกแบบให้ exo มี “handling quality” เดียวกันในหลาย payload
     - ใส่ load/torque envelope protection
     - ไม่ให้ force amplification เป็นแค่ gain คงที่อย่างเดียว

### อันดับ 3: Active inceptor และ haptic feedback

5. **Design and Evaluation of a Flight Envelope Protection Haptic Feedback System**
   - ผู้เขียน: Joost Ellerbroek, Mitchell Rodriguez Martin, T. Lombaerts, Rene van Paassen, Max Mulder
   - แหล่ง: IFAC-PapersOnLine / TU Delft
   - DOI: 10.1016/j.ifacol.2016.10.481
   - ลิงก์: https://repository.tudelft.nl/file/File_56c999ed-89ad-493f-b3ac-60973bdb5c3d?preview=1
   - ประเด็นหลัก: shared control, haptic feedback, stiffness feedback, vibration cue, flight envelope protection
   - เอามาใช้กับเรา:
     - เมื่อแขนใกล้มุม/torque limit ให้ exo เพิ่ม stiffness หรือสั่นเตือน
     - แทนที่จะตัดแรงช่วยทันที ให้ cue ผู้ใช้ก่อน
     - ใช้ haptic cue บอกว่า controller กำลัง override หรือจำกัดแรง

6. **Definition and Verification of Active Inceptor Requirements for a Future Tiltrotor**
   - ผู้เขียน: Raphael Burgmair, Adrian Alford, Stephen Mouritsen
   - แหล่ง: European Rotorcraft Forum
   - ลิงก์: https://dspace-erf.nlr.nl/server/api/core/bitstreams/f6a449e9-1f82-4232-92c6-69222b9d6fdd/content
   - ประเด็นหลัก: active inceptors, adjustable tactile information, force-deflection characteristics, limit cues, piloted simulation
   - เอามาใช้กับเรา:
     - exo cuff/handle อาจทำหน้าที่เหมือน active inceptor ของแขน
     - ต้องออกแบบ force feedback ไม่ใช่แค่ motor assist
     - tactile bandwidth สำคัญ: cue ต้องเร็วพอและไม่สั่นหลอก

### อันดับ 4: fault tolerance, certification thinking, failure cases

7. **Modeling the Fault Tolerant Capability of a Flight Control System: An Exercise in SCR Specification**
   - แหล่ง: NASA NTRS
   - ลิงก์: https://ntrs.nasa.gov/citations/20000055721
   - ประเด็นหลัก: fault tolerance for sensor faults in flight control systems
   - เอามาใช้กับเรา:
     - สร้าง fault table สำหรับ exo:
       - load cell stuck high
       - encoder wrong sign
       - motor driver stuck torque
       - sensor dropout
       - battery undervoltage
     - ระบบต้อง downgrade เป็น safe mode ไม่ใช่ช่วยแรงต่อ

8. **FAA AC 25.671-1 Flight Control Systems**
   - แหล่ง: FAA
   - ลิงก์: https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_25.671-1.pdf
   - ประเด็นหลัก: flight control operation, failure evaluation, control authority awareness, submodes, jams
   - เอามาใช้กับเรา:
     - แม้ exo ไม่ใช่เครื่องบิน แต่แนวคิดดีมาก:
       - ต้องประเมิน jam
       - ต้องประเมิน wrong-direction control
       - ต้องมี alert เมื่อ mode เปลี่ยน
       - ต้องบอกผู้ใช้เมื่อ control authority ใกล้หมด

### อ่านเสริม

9. **The Fly-by-Wire System**
   - แหล่ง: INCAS Bulletin
   - ลิงก์: https://bulletin.incas.ro/files/nicolin-i__nicolin-b-a__vol_11_iss_4.pdf
   - ประเด็น: overview ประวัติ fly-by-wire
   - ใช้เป็น introduction ได้ แต่ไม่ใช่ตัวหลักด้าน control design

10. **The Story of Self-Repairing Flight Control Systems**
   - แหล่ง: NASA
   - ลิงก์: https://www.nasa.gov/wp-content/uploads/2021/04/88798main_srfcs.pdf
   - ประเด็น: self-repairing / adaptive flight control history
   - ใช้เป็นแรงบันดาลใจเรื่อง fault recovery แต่ยังไกลจาก prototype exo ตอนนี้

## 3. หลักการจาก fly-by-wire ที่ควรเอามาใส่ exo

### 3.1 เปลี่ยนชื่อ architecture เป็น Arm-by-Wire

เสนอ architecture:

```text
Human input layer
  - cuff force
  - joint angle
  - joint velocity
  - optional EMG/handle force

Intent estimation layer
  - human-only effort estimate
  - motor torque observer subtraction
  - sensor plausibility checks

Control law layer
  - force amplification
  - gravity compensation
  - impedance/admittance
  - torque rate limiting

Envelope protection layer
  - joint angle limits
  - joint velocity limits
  - torque limits
  - power/current limits
  - pain/pressure/cuff-force limits

Actuator allocation layer
  - shoulder torque command
  - elbow torque command
  - motor driver command

Feedback layer
  - haptic stiffness
  - vibration warning
  - visual/audio status
  - safe mode indication
```

### 3.2 Control laws ต้องมี modes

จาก fly-by-wire เราไม่ควรมีแค่ `force_amp on/off` แต่ควรมี control law modes:

```text
DIRECT
  motor follows low-level torque command, bench only

ASSIST_NORMAL
  force amplification + gravity compensation + envelope protection

ASSIST_LIMITED
  lower torque limit after sensor disagreement or thermal warning

SAFE_DAMPING
  motor provides damping only, no lift assist

PASSIVE
  motor disabled/backdrivable if possible

FAULT_LOCKOUT
  e-stop or serious fault, driver disabled
```

### 3.3 Envelope protection สำหรับแขน

เครื่องบินมี flight envelope; แขนเราควรมี arm safety envelope:

```text
angle envelope:
  shoulder -20 to 110 deg active
  elbow 0 to 135 deg active

torque envelope:
  shoulder early human cap 20 Nm
  elbow early human cap 8 Nm

velocity envelope:
  max joint velocity before damping mode

power envelope:
  current limit, battery voltage, driver temperature

interaction envelope:
  cuff force / pressure threshold
```

### 3.4 Haptic cue สำคัญมาก

FBW มีปัญหาคล้ายกันคือ เมื่อ computer จำกัด input ผู้ใช้ต้องรู้ ไม่งั้นจะรู้สึกว่าระบบ “ขัดใจ” หรือ “ไม่ตอบสนอง”

สำหรับ exo:

- ถ้าใกล้มุม limit: เพิ่ม virtual stiffness
- ถ้า torque เกิน limit: สั่นเบา ๆ หรือเพิ่ม resistance
- ถ้า sensor disagree: ลด assist และแจ้ง status
- ถ้าระบบเข้า safe mode: ให้ feedback ชัดเจน ไม่เงียบ

### 3.5 Iron bird ก่อน hardware ใส่คน

NASA F-8 ใช้ iron bird simulator ก่อน flight test แนวคิดนี้ควรใช้กับเรา:

```text
exo iron bird:
  dummy upper arm
  dummy forearm
  real motor/driver
  real load cell
  real controller
  simulated payload
  emergency stop
```

เป้าหมายคือให้ control loop และ fault handling ผ่าน bench test ก่อนใส่กับคน

## 4. ข้อเสนอ experiment ถัดไป

### Experiment A: Arm-by-wire modes

เพิ่ม `control_law_mode` ใน simulation:

```text
direct
assist_normal
assist_limited
safe_damping
fault_lockout
```

วัด:

- tracking error
- peak human torque
- motor saturation
- transition smoothness

### Experiment B: Envelope protection

จำลองกรณีผู้ใช้พยายามยกเร็วเกินหรือมุมเกิน limit:

```text
no protection
soft limit
hard limit
haptic cue + soft limit
```

วัด:

- overshoot
- torque spike
- user effort spike
- mode transition jerk

### Experiment C: Sensor fault tolerance

ต่อจาก bad sensor ที่เราทำแล้ว:

```text
load cell stuck high
load cell stuck low
encoder sign reversed
encoder dropout
motor current mismatch
sensor delay 30/80/150 ms
```

วัด:

- detect time
- peak unsafe torque
- safe-mode entry time
- remaining controllability

### Experiment D: Haptic cue

จำลอง haptic cue:

```text
virtual stiffness near limit
vibration cue near torque limit
center-shift cue toward safe posture
```

สำหรับแขนจริงอาจแปลงเป็น:

- เพิ่ม damping
- เพิ่ม resistance เมื่อใกล้มุมอันตราย
- ลด assist อย่างนุ่ม

## 5. สรุป paper ที่ควรอ่านก่อน

ถ้าอ่านแค่ 4 ชิ้นแรก ให้เรียงแบบนี้:

1. NASA F-8 Design and Development Experience
2. NASA F-8 Flight Test Experience
3. Fly-by-Wire Augmented Manual Control - Basic Design Considerations
4. Design and Evaluation of a Flight Envelope Protection Haptic Feedback System

ถ้าเน้นนำไปใช้กับ exo ทันที:

```text
F-8 papers -> เอา architecture, iron bird, monitoring
FBW augmented manual control -> เอา mode/neutral behavior
haptic FEP paper -> เอา soft limit + haptic cue
fault tolerance paper/FAA AC -> เอา failure table + safe mode
```

## 6. Design translation สำหรับงานเรา

ชื่อแนวคิดที่เสนอ:

```text
Arm-by-Wire Assist Control
```

หลักการ:

```text
มนุษย์ไม่ได้สั่งมอเตอร์ตรง ๆ
มนุษย์ส่ง intent ผ่านแรง/มุม/การเคลื่อนที่
controller แปลง intent เป็น torque command
ก่อนส่งให้มอเตอร์ต้องผ่าน safety envelope และ fault checks
ถ้าใกล้ limit ต้องแจ้งผู้ใช้ผ่าน haptic cue หรือ force feedback
ถ้า sensor ไม่น่าเชื่อถือ ต้อง downgrade mode
```

สิ่งนี้ตรงกับปัญหาใหญ่ของเราในตอนนี้: force amplification ใช้ได้เฉพาะเมื่อ sensor estimate เป็น human-only จริง ถ้าไม่จริง ต้องให้ระบบ detect แล้วลด mode ทันที
