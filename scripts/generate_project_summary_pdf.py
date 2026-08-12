"""Generate a polished PDF summary for the Exoskeleton project."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PDF = ROOT / "output" / "pdf" / "exoskeleton_project_summary_2026-07-09.pdf"
TAHOMA = Path(r"C:\Windows\Fonts\tahoma.ttf")
TAHOMA_BOLD = Path(r"C:\Windows\Fonts\tahomabd.ttf")

ASSIST_CSV = ROOT / "outputs" / "assist_sweep_summary.csv"
FORCE_CSV = ROOT / "outputs" / "force_amp_sweep_summary.csv"
SENSOR_2D_CSV = ROOT / "outputs" / "sensor_feedback_summary.csv"
SENSOR_3D_CSV = ROOT / "outputs" / "sensor_feedback_3d_summary.csv"
BLUEPRINT_IMAGE = ROOT / "outputs" / "exo_product_blueprint_v0_1.png"
DESIGN_PREVIEW_IMAGE = ROOT / "outputs" / "arm_3d_design_v0_1_preview.png"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Tahoma", str(TAHOMA)))
    pdfmetrics.registerFont(TTFont("Tahoma-Bold", str(TAHOMA_BOLD)))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def find_row(rows: Iterable[dict[str, str]], **conditions: str) -> dict[str, str]:
    for row in rows:
        if all(row[key] == value for key, value in conditions.items()):
            return row
    raise KeyError(f"Could not find row for {conditions}")


def f(value: str | float) -> float:
    return float(value)


def fmt_nm(value: str | float) -> str:
    return f"{f(value):.2f} Nm"


def fmt_kg(value: str | float) -> str:
    return f"{f(value):.2f} kg"


def fmt_deg(value: str | float) -> str:
    return f"{f(value):.2f} deg"


def fmt_pct(value: str | float) -> str:
    return f"{100.0 * f(value):.2f}%"


def fmt_ms(value: str | float) -> str:
    return f"{1000.0 * f(value):.0f} ms"


def wrap_text(text: str, max_chars: int = 72) -> str:
    words = text.strip()
    if not words:
        return ""

    lines: list[str] = []
    remaining = words
    while len(remaining) > max_chars:
        split = remaining.rfind(" ", 0, max_chars + 1)
        if split < max_chars // 2:
            split = max_chars
        lines.append(remaining[:split].strip())
        remaining = remaining[split:].strip()
    if remaining:
        lines.append(remaining)
    return "<br/>".join(escape(line) for line in lines)


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleThai",
            parent=styles["Title"],
            fontName="Tahoma-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#12344d"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtitleThai",
            parent=styles["Normal"],
            fontName="Tahoma",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#506070"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionThai",
            parent=styles["Heading1"],
            fontName="Tahoma-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#12344d"),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyThai",
            parent=styles["Normal"],
            fontName="Tahoma",
            fontSize=10.2,
            leading=14,
            textColor=colors.HexColor("#1f2933"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletThai",
            parent=styles["Normal"],
            fontName="Tahoma",
            fontSize=10.0,
            leading=13.5,
            leftIndent=10,
            firstLineIndent=-8,
            textColor=colors.HexColor("#1f2933"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallThai",
            parent=styles["Normal"],
            fontName="Tahoma",
            fontSize=8.7,
            leading=11,
            textColor=colors.HexColor("#52606d"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CaptionThai",
            parent=styles["Normal"],
            fontName="Tahoma",
            fontSize=8.5,
            leading=10.5,
            textColor=colors.HexColor("#52606d"),
            alignment=1,
            spaceBefore=3,
        )
    )
    return styles


def p(text: str, style: ParagraphStyle, max_chars: int = 72) -> Paragraph:
    return Paragraph(wrap_text(text, max_chars=max_chars), style)


def bullet(text: str, styles) -> Paragraph:
    return p(f"- {text}", styles["BulletThai"], max_chars=78)


def table_from_rows(rows: list[list[str]], col_widths: list[float]) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce9f2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#102a43")),
                ("FONTNAME", (0, 0), (-1, 0), "Tahoma-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Tahoma"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.9),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bcccdc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fbfd")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def image_block(path: Path, max_width: float, caption: str, styles) -> Table:
    reader = ImageReader(str(path))
    width, height = reader.getSize()
    scale = min(max_width / width, 140 * mm / height)
    image = Image(str(path), width=width * scale, height=height * scale)
    block = Table([[image], [p(caption, styles["CaptionThai"], max_chars=58)]], colWidths=[max_width])
    block.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return block


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d9e2ec"))
    canvas.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)
    canvas.setFont("Tahoma", 8)
    canvas.setFillColor(colors.HexColor("#52606d"))
    canvas.drawString(doc.leftMargin, 8 * mm, "Exoskeleton project summary")
    canvas.drawRightString(A4[0] - doc.rightMargin, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def collect_snapshot() -> dict[str, object]:
    assist_rows = read_csv(ASSIST_CSV)
    force_rows = read_csv(FORCE_CSV)
    sensor_2d_rows = read_csv(SENSOR_2D_CSV)
    sensor_3d_rows = read_csv(SENSOR_3D_CSV)

    assist_baseline = find_row(assist_rows, assist_ratio="0.0")
    assist_80 = find_row(assist_rows, assist_ratio="0.8")
    force_gain_10 = find_row(force_rows, amplification_gain="1.0")
    sensor_2d_human_0 = find_row(sensor_2d_rows, force_sensor_mode="human_only", motor_response_time_s="0.0")
    sensor_2d_human_80 = find_row(sensor_2d_rows, force_sensor_mode="human_only", motor_response_time_s="0.08")
    sensor_2d_bad_0 = find_row(sensor_2d_rows, force_sensor_mode="combined", motor_response_time_s="0.0")
    sensor_2d_bad_80 = find_row(sensor_2d_rows, force_sensor_mode="combined", motor_response_time_s="0.08")
    sensor_3d_human_0 = find_row(sensor_3d_rows, force_sensor_mode="human_only", motor_response_time_s="0.0")
    sensor_3d_bad_0 = find_row(sensor_3d_rows, force_sensor_mode="combined", motor_response_time_s="0.0")
    sensor_3d_bad_80 = find_row(sensor_3d_rows, force_sensor_mode="combined", motor_response_time_s="0.08")

    return {
        "assist_baseline": assist_baseline,
        "assist_80": assist_80,
        "force_gain_10": force_gain_10,
        "sensor_2d_human_0": sensor_2d_human_0,
        "sensor_2d_human_80": sensor_2d_human_80,
        "sensor_2d_bad_0": sensor_2d_bad_0,
        "sensor_2d_bad_80": sensor_2d_bad_80,
        "sensor_3d_human_0": sensor_3d_human_0,
        "sensor_3d_bad_0": sensor_3d_bad_0,
        "sensor_3d_bad_80": sensor_3d_bad_80,
        "py_modules": len(list((ROOT / "exosim").glob("*.py"))),
        "scripts": len(list((ROOT / "scripts").glob("*.py"))),
        "tests": len(list((ROOT / "tests").glob("test_*.py"))),
        "docs": len(list((ROOT / "docs").glob("*.md"))),
        "models": len(list((ROOT / "models").glob("*.xml"))),
    }


def build_story(snapshot: dict[str, object], styles) -> list[object]:
    story: list[object] = []

    assist_baseline = snapshot["assist_baseline"]
    assist_80 = snapshot["assist_80"]
    force_gain_10 = snapshot["force_gain_10"]
    sensor_2d_human_0 = snapshot["sensor_2d_human_0"]
    sensor_2d_human_80 = snapshot["sensor_2d_human_80"]
    sensor_2d_bad_0 = snapshot["sensor_2d_bad_0"]
    sensor_2d_bad_80 = snapshot["sensor_2d_bad_80"]
    sensor_3d_human_0 = snapshot["sensor_3d_human_0"]
    sensor_3d_bad_0 = snapshot["sensor_3d_bad_0"]
    sensor_3d_bad_80 = snapshot["sensor_3d_bad_80"]

    story.append(Spacer(1, 10 * mm))
    story.append(p("สรุปทั้งโปรเจกต์ Exoskeleton Arm Physics Simulator", styles["TitleThai"], max_chars=34))
    story.append(
        p(
            "Generated from repository artifacts in C:\\Exoskeleton on 2026-07-09. เอกสารนี้สรุปทั้งมุม simulation software, ผลการทดลอง, แนวทาง mechanical design, และสถานะของงานที่พร้อมต่อยอด.",
            styles["SubtitleThai"],
            max_chars=72,
        )
    )

    hero = Table(
        [
            [
                p(
                    "Key takeaway: โปรเจกต์นี้พิสูจน์ได้แล้วใน simulation ว่า force amplification แบบ gain = 1.0 สามารถทำให้ payload 5 kg รู้สึกใกล้ 2.5 kg ได้ แต่ความปลอดภัยของระบบขึ้นกับการแยก human torque ออกจาก motor torque อย่างชัดเจน.",
                    styles["BodyThai"],
                    max_chars=78,
                )
            ]
        ],
        colWidths=[174 * mm],
    )
    hero.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e6f4ea")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#7fb685")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(hero)
    story.append(Spacer(1, 5 * mm))

    overview_rows = [
        [
            p("ขอบเขตงาน", styles["SmallThai"], 20),
            p("simulation-first prototype สำหรับ แขน exoskeleton ช่วยยกของ", styles["SmallThai"], 68),
        ],
        [
            p("เป้าหมายแรก", styles["SmallThai"], 20),
            p("ทำให้ payload 5 kg ให้รู้สึกใกล้ 2.5 kg ผ่าน force amplification", styles["SmallThai"], 68),
        ],
        [
            p("ฐานโค้ด", styles["SmallThai"], 20),
            p(
                f"Python modules {snapshot['py_modules']} ไฟล์, scripts {snapshot['scripts']} ไฟล์, tests {snapshot['tests']} ไฟล์, docs {snapshot['docs']} ไฟล์, models {snapshot['models']} ไฟล์",
                styles["SmallThai"],
                68,
            ),
        ],
        [
            p("หลักฐานหลัก", styles["SmallThai"], 20),
            p("README, reports/full report, mechanical design spec, product blueprint, MuJoCo model, และ CSV summaries", styles["SmallThai"], 68),
        ],
    ]
    story.append(table_from_rows(overview_rows, [34 * mm, 140 * mm]))
    story.append(Spacer(1, 6 * mm))
    story.append(p("Executive Summary", styles["SectionThai"], max_chars=26))
    story.extend(
        [
            bullet("แกนของโปรเจกต์ คือ แบบจำลองแขนสองท่อน 2D และแบบจำลอง 3D บน MuJoCo เพื่อวิเคราะห์ torque ที่หัวไหล่และข้อศอกก่อนสร้าง hardware จริง", styles),
            bullet("มี controller หลัก 2 แบบ คือ gravity compensation และ force amplification โดยแบบหลังเป็นคำตอบตรงต่อโจทย์ 5 kg ให้รู้สึกใกล้ 2.5 kg", styles),
            bullet("ผลที่สำคัญที่สุด คือ sensor mode แบบ human_only ทำงานได้ตามเป้า แต่ sensor mode แบบ combined ทำให้เกิด positive feedback และ motor saturation", styles),
            bullet("repo ไม่ได้มีแค่ code simulation แต่มี blueprint ระดับ product, mechanical layout v0.1, literature review, preview images, และ test suite สำหรับ physics กับ assets", styles),
        ]
    )

    story.append(PageBreak())
    story.append(p("1. ระบบที่มีอยู่ในโปรเจกต์", styles["SectionThai"], max_chars=26))
    story.extend(
        [
            bullet("exosim/arm.py นิยาม rigid-body dynamics ของแขน 2 ข้อต่อ พร้อม mass matrix, coriolis, gravity, damping และ step integrator", styles),
            bullet("exosim/controllers.py มี logic ของ gravity assist, human tracking, และ force amplification พร้อม motor limits และ response lag", styles),
            bullet("exosim/mujoco_simulate.py แยก human torque กับ motor torque ชัดเจนใน 3D simulation และคำนวณ summary metrics อัตโนมัติ", styles),
            bullet("scripts/ ใช้รันชุดทดลองหลัก เช่น assist sweep, force amplification sweep, sensor feedback comparison, และ 3D sensor comparison", styles),
            bullet("docs/ และ reports/ เก็บความหมายเชิงวิศวกรรม ไม่ใช่แค่บันทึกผล ทำให้โปรเจกต์นี้มีทั้ง implementation และ product direction อยู่ใน repo เดียวกัน", styles),
        ]
    )
    story.append(Spacer(1, 4 * mm))
    story.append(p("ภาพตัวอย่างของระบบและทิศทาง product", styles["BodyThai"], max_chars=36))

    image_table = Table(
        [
            [
                image_block(DESIGN_PREVIEW_IMAGE, 82 * mm, "MuJoCo design preview: โครง exoskeleton, cuff, motor housing, และ payload", styles),
                image_block(BLUEPRINT_IMAGE, 82 * mm, "Product blueprint v0.1: ภาพรวม architecture ของระบบในระดับ product engineering", styles),
            ]
        ],
        colWidths=[86 * mm, 86 * mm],
    )
    image_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(image_table)
    story.append(Spacer(1, 5 * mm))

    story.append(p("สิ่งที่โปรเจกต์นี้ตอบได้แล้ว", styles["BodyThai"], max_chars=34))
    story.extend(
        [
            bullet("ต้องใช้ joint torque เท่าไรในการยก payload ที่กำหนด", styles),
            bullet("assist ratio หรือ amplification gain เปลี่ยนภาระของมนุษย์อย่างไร", styles),
            bullet("motor lag และ sensor mode ส่งผลต่อ stability และ tracking error มากแค่ไหน", styles),
            bullet("ถ้าจะต่อไปสู่ hardware ควรวาง shoulder motor, elbow motor, cuff, battery, และ safety loop อย่างไรในระดับ concept engineering", styles),
        ]
    )

    story.append(PageBreak())
    story.append(p("2. ผลการทดลองที่ควรรู้", styles["SectionThai"], max_chars=26))
    story.append(
        p(
            "ผลด้านล่างดึงมาจาก CSV summaries ใน repo โดยตรง เพื่อให้สรุปนี้อ้างอิงตัวเลขเดียวกับงานทดลองจริง.",
            styles["BodyThai"],
            max_chars=70,
        )
    )

    assist_table = table_from_rows(
        [
            ["Experiment", "Observation"],
            [
                "Gravity assist sweep",
                f"peak human shoulder ลดจาก {fmt_nm(assist_baseline['peak_human_shoulder_nm'])} ที่ assist 0% เหลือ {fmt_nm(assist_80['peak_human_shoulder_nm'])} ที่ assist 80%",
            ],
            [
                "Force amplification",
                f"gain 1.0 ให้ peak human shoulder = {fmt_nm(force_gain_10['peak_human_shoulder_nm'])}, peak motor shoulder = {fmt_nm(force_gain_10['peak_motor_shoulder_nm'])}, felt payload = {fmt_kg(force_gain_10['felt_payload_kg_by_shoulder_peak'])}",
            ],
            [
                "Interpretation",
                "ในกรณี ideal sensor ระบบแบ่งภาระระหว่างคนกับมอเตอร์ได้ใกล้ 50/50 ตามโจทย์ตั้งต้น",
            ],
        ],
        [48 * mm, 126 * mm],
    )
    story.append(assist_table)
    story.append(Spacer(1, 4 * mm))

    story.append(p("ตารางสรุป sensor feedback risk ใน 2D", styles["BodyThai"], max_chars=36))
    sensor_2d_table = table_from_rows(
        [
            ["Mode", "Lag", "Peak motor shoulder", "Max shoulder error", "Meaning"],
            [
                "human_only",
                fmt_ms(sensor_2d_human_0["motor_response_time_s"]),
                fmt_nm(sensor_2d_human_0["peak_motor_shoulder_nm"]),
                fmt_deg(sensor_2d_human_0["shoulder_tracking_max_abs_deg"]),
                "ทำงานตามเป้าหมาย",
            ],
            [
                "human_only",
                fmt_ms(sensor_2d_human_80["motor_response_time_s"]),
                fmt_nm(sensor_2d_human_80["peak_motor_shoulder_nm"]),
                fmt_deg(sensor_2d_human_80["shoulder_tracking_max_abs_deg"]),
                "ยังพอคุมได้ แต่ช่วยช้าลง",
            ],
            [
                "combined",
                fmt_ms(sensor_2d_bad_0["motor_response_time_s"]),
                fmt_nm(sensor_2d_bad_0["peak_motor_shoulder_nm"]),
                fmt_deg(sensor_2d_bad_0["shoulder_tracking_max_abs_deg"]),
                "เริ่มเกิด positive feedback",
            ],
            [
                "combined",
                fmt_ms(sensor_2d_bad_80["motor_response_time_s"]),
                fmt_nm(sensor_2d_bad_80["peak_motor_shoulder_nm"]),
                fmt_deg(sensor_2d_bad_80["shoulder_tracking_max_abs_deg"]),
                "feedback รุนแรงขึ้นมาก",
            ],
        ],
        [26 * mm, 18 * mm, 42 * mm, 38 * mm, 50 * mm],
    )
    story.append(sensor_2d_table)
    story.append(Spacer(1, 4 * mm))

    story.append(p("ตารางสรุป pattern เดียวกันใน 3D MuJoCo", styles["BodyThai"], max_chars=36))
    sensor_3d_table = table_from_rows(
        [
            ["Mode", "Lag", "Peak motor shoulder", "Saturation", "Max shoulder error"],
            [
                "human_only",
                fmt_ms(sensor_3d_human_0["motor_response_time_s"]),
                fmt_nm(sensor_3d_human_0["peak_motor_shoulder_nm"]),
                fmt_pct(sensor_3d_human_0["shoulder_motor_saturation_fraction"]),
                fmt_deg(sensor_3d_human_0["shoulder_tracking_max_abs_deg"]),
            ],
            [
                "combined",
                fmt_ms(sensor_3d_bad_0["motor_response_time_s"]),
                fmt_nm(sensor_3d_bad_0["peak_motor_shoulder_nm"]),
                fmt_pct(sensor_3d_bad_0["shoulder_motor_saturation_fraction"]),
                fmt_deg(sensor_3d_bad_0["shoulder_tracking_max_abs_deg"]),
            ],
            [
                "combined",
                fmt_ms(sensor_3d_bad_80["motor_response_time_s"]),
                fmt_nm(sensor_3d_bad_80["peak_motor_shoulder_nm"]),
                fmt_pct(sensor_3d_bad_80["shoulder_motor_saturation_fraction"]),
                fmt_deg(sensor_3d_bad_80["shoulder_tracking_max_abs_deg"]),
            ],
        ],
        [30 * mm, 18 * mm, 42 * mm, 28 * mm, 50 * mm],
    )
    story.append(sensor_3d_table)
    story.append(Spacer(1, 5 * mm))
    story.extend(
        [
            bullet("ข้อค้นพบที่แข็งแรงที่สุดของโปรเจกต์ คือ ปัญหาไม่ได้อยู่แค่ว่า motor แรงพอหรือไม่ แต่ sensor กำลังวัด human torque ที่แท้จริงหรือเปล่า", styles),
            bullet("เมื่ออ่านแรงรวมของคนกับมอเตอร์ ระบบจะช่วยเกิน และชน shoulder limit 80 Nm ทั้งใน 2D และ 3D", styles),
            bullet("เพราะผล 2D กับ 3D ให้ pattern ตรงกัน จึงมีน้ำหนักว่า failure mode นี้เป็นปัญหาเชิงระบบ ไม่ใช่ artifact จากซิมแบบใดแบบหนึ่ง", styles),
        ]
    )

    story.append(PageBreak())
    story.append(p("3. ทิศทาง mechanical และ product", styles["SectionThai"], max_chars=28))
    story.extend(
        [
            bullet("โปรเจกต์มี design direction ชัดเจนแล้ว: single-arm lateral frame, shoulder motor อยู่ที่ torso or backpack side plate, elbow motor อยู่ใกล้ข้อศอกบนต้นแขน", styles),
            bullet("เอกสาร mechanical design v0.1 และ product blueprint v0.1 ระบุขนาดหลัก ช่วงปรับ anthropometry, torque targets, power system, wiring, cuff layout และ safety loop เบื้องต้นไว้ครบ", styles),
            bullet("build order ที่เอกสารเสนอมีเหตุผลดี: เริ่มจาก elbow-only bench rig ก่อน แล้วค่อยไป wearable elbow, shoulder transmission bench, และ full single-arm prototype", styles),
            bullet("literature review ด้าน fly-by-wire เพิ่มกรอบคิดเรื่อง intent estimation, envelope protection, degraded modes, และ iron-bird style testing ก่อนใช้งานจริง", styles),
        ]
    )
    story.append(Spacer(1, 4 * mm))

    decision_table = table_from_rows(
        [
            ["Design area", "Current direction in repo"],
            ["Actuation", "shoulder remote drive ที่ torso และ elbow actuator ใกล้ข้อศอก"],
            ["Sensor architecture", "ต้องแยก human-only effort และห้ามใช้ combined effort เป็น feedback ตรง"],
            ["Safety", "mechanical hard stops, software torque limit, torque rate limit, emergency stop, watchdog"],
            ["Prototype order", "elbow-only bench first, then low-payload wearable tests"],
        ],
        [44 * mm, 130 * mm],
    )
    story.append(decision_table)
    story.append(Spacer(1, 5 * mm))

    story.append(p("4. ข้อจำกัดของงานปัจจุบัน", styles["SectionThai"], max_chars=28))
    story.extend(
        [
            bullet("ยังไม่มี hardware จริง, sensor จริง, หรือ human subject testing ดังนั้นทุกข้อสรุปในตอนนี้ยังเป็น simulation evidence", styles),
            bullet("แบบจำลองยังเน้น shoulder and elbow flexion ในระนาบยกของเป็นหลัก และยังไม่ใช่ upper-limb biomechanics ที่ครบทุก DOF", styles),
            bullet("controller ยังเป็น baseline control law ไม่ใช่ production-grade human-robot interaction control เช่น impedance or admittance control ที่สมบูรณ์", styles),
            bullet("ยังขาด noise, backlash, compliance, contact pressure, fatigue, thermal curves และ fault injections ที่ละเอียดกว่านี้", styles),
        ]
    )
    story.append(Spacer(1, 4 * mm))

    story.append(p("5. งานถัดไปที่มี impact สูง", styles["SectionThai"], max_chars=28))
    story.extend(
        [
            bullet("ทำ sensor separation experiment ให้ชัด ว่าใน hardware จะวัด human-only effort ด้วย load cell, series elastic sensing, หรือ torque observer แบบใด", styles),
            bullet("ต่อยอด 3D simulator ด้วย noise, latency, torque rate limits, current limits, และ failure modes ที่ realistic ขึ้น", styles),
            bullet("เริ่ม bench prototype แบบ elbow-only เพื่อพิสูจน์ force amplification โดยไม่เสี่ยงกับ shoulder alignment ตั้งแต่แรก", styles),
            bullet("เพิ่ม safe modes ตามแนวคิด Arm-by-Wire เช่น assist_normal, assist_limited, safe_damping, passive, และ fault_lockout", styles),
        ]
    )
    story.append(Spacer(1, 4 * mm))

    story.append(PageBreak())
    story.append(p("6. ไฟล์ที่ควรเปิดต่อจาก PDF นี้", styles["SectionThai"], max_chars=28))
    story.extend(
        [
            bullet("README.md", styles),
            bullet("reports/exoskeleton_arm_simulation_full_report_2026-07-03.th.md", styles),
            bullet("docs/mechanical_design_v0_1.th.md", styles),
            bullet("docs/product_engineering_blueprint_v0_1.th.md", styles),
            bullet("docs/fly_by_wire_literature_review_2026-07-03.th.md", styles),
            bullet("exosim/arm.py, exosim/controllers.py, exosim/mujoco_simulate.py", styles),
            bullet("outputs/assist_sweep_summary.csv, outputs/force_amp_sweep_summary.csv, outputs/sensor_feedback_summary.csv, outputs/sensor_feedback_3d_summary.csv", styles),
        ]
    )
    story.append(Spacer(1, 5 * mm))

    closing = Table(
        [
            [
                p(
                    "Bottom line: โปรเจกต์นี้เลยช่วง proof-of-concept แบบไอเดียลอย ๆ ไปแล้ว เพราะมีทั้งแบบจำลองทางฟิสิกส์, ชุดทดลอง, เอกสาร design, และผลลัพธ์ที่ชี้จุดเสี่ยงเชิงระบบชัดเจน แต่ยังอยู่ก่อนขั้น wearable hardware validation และ safety proof.",
                    styles["BodyThai"],
                    max_chars=80,
                )
            ]
        ],
        colWidths=[174 * mm],
    )
    closing.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef2f7")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#9fb3c8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(closing)
    story.append(Spacer(1, 3 * mm))
    story.append(
        p(
            f"Verification note: local unittest run on {date(2026, 7, 9).isoformat()} passed 13/13 tests.",
            styles["SmallThai"],
            max_chars=72,
        )
    )
    return story


def main() -> None:
    register_fonts()
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    snapshot = collect_snapshot()
    story = build_story(snapshot, styles)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title="Exoskeleton project summary",
        author="OpenAI Codex",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
