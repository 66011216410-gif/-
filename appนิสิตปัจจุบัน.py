import io
import re
from copy import copy

import pandas as pd
import streamlit as st

st.set_page_config(page_title="ระบบสถิตินิสิตบัณฑิตศึกษา", page_icon="📊", layout="wide")


# พื้นหลังเว็บจากภาพอาคาร — วางภาพไว้ชั้นบนสุดและให้เนื้อหาอยู่เหนือภาพ
st.markdown(
    """
    <style>
    /* พื้นหลังเว็บจากภาพต้นฉบับความละเอียดสูง */
    html, body {
        background: transparent !important;
    }

    body::before {
        content: "";
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        background-image: url("data:image/webp;base64,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");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        opacity: 0.38;
        z-index: 0;
        pointer-events: none;
    }

    .stApp,
    div[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewContainer"] > div,
    div[data-testid="stAppViewContainer"] .main,
    section[data-testid="stMain"],
    div[data-testid="stMainBlockContainer"] {
        background: transparent !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    section[data-testid="stMain"],
    div[data-testid="stMainBlockContainer"] {
        position: relative;
        z-index: 1;
    }

    .dashboard-box {
        background: rgba(243, 247, 252, 0.90);
        padding: 18px 10px 22px 10px;
        margin-bottom: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

REQUIRED_COLUMNS = [
    "ปีที่เข้า", "ภาคการศึกษาที่เข้า", "รหัสนิสิต", "คณะ", "วิทยาเขต", "สาขา",
    "ระดับ", "รหัสสถานะนิสิต", "สถานะนิสิต", "ปีที่จบ", "เทอมที่จบ", "วันที่จบ"
]

# สถานะที่ต้องไม่นำมาคำนวณสถิติ 4 ช่องใหม่
STATUS_EXCLUDE = ["พ้นสภาพ (เสียชีวิต)", "พ้นสภาพ", "ลาออก"]

STATUS_DISPLAY = [
    "นิสิตปัจจุบัน", "พ้นสภาพ (คณบดีอนุมัติ)", "พ้นสภาพ (เสียชีวิต)",
    "พ้นสภาพ", "รักษาสภาพนิสิต", "ลาพักการเรียน", "ลาออก"
]


def clean_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()


def num(x):
    try:
        return float(x)
    except Exception:
        return None


def calc_duration(row):
    """1 เทอม = 0.5 ปี และภาคเดียวกันของปีเดียวกัน = 0.5 ปี"""
    y0, s0 = num(row.get("ปีที่เข้า")), num(row.get("ภาคการศึกษาที่เข้า"))
    y1, s1 = num(row.get("ปีที่จบ")), num(row.get("เทอมที่จบ"))
    if None in (y0, s0, y1, s1):
        return None
    semesters = (y1 - y0) * 2 + (s1 - s0) + 1
    d = semesters * 0.5
    return round(d, 1) if d > 0 else None


def normalize_level(x):
    x = clean_text(x)
    if "เอก" in x:
        return "ป.เอก"
    if "โท" in x:
        return "ป.โท"
    return x or "ไม่ระบุ"


def status_group(x):
    s = clean_text(x)

    # กลุ่ม "พ้นสภาพ" ต้องตรวจสอบก่อนสถานะอื่น
    # เพราะบางข้อความมีคำว่า "สำเร็จการศึกษา", "รักษาสภาพ" หรือ "ลาพัก" อยู่ภายใน
    if (
        s == "นิสิตที่ไม่มารายงานตัว"
        or any(
            code in s
            for code in [
                "38.4 ",
                "38.4.1 ",
                "38.4.12 ",
                "38.4.14 ",
                "38.4.2 ",
                "38.4.3 ",
                "38.4.4 ",
                "38.4.5 ",
                "38.4.6 ",
                "38.4.8 ",
                "38.6 ",
                "38.7 ",
            ]
        )
    ):
        return "พ้นสภาพ"

    # รวม 37.3 และ 38.3 เป็น "พ้นสภาพ (คณบดีอนุมัติ)"
    if (
        "37.3 ลาออกโดยได้รับอนุมัติจากคณบดีบัณฑิตวิทยาลัย" in s
        or "38.3 ลาออกโดยได้รับอนุมัติจากคณบดีบัณฑิตวิทยาลัย" in s
    ):
        return "พ้นสภาพ (คณบดีอนุมัติ)"

    # รวม 19.1 และ 37.2 เป็น "พ้นสภาพ (เสียชีวิต)"
    if "19.1 ตาย" in s or "37.2 ตาย" in s:
        return "พ้นสภาพ (เสียชีวิต)"
    if "เสียชีวิต" in s:
        return "พ้นสภาพ (เสียชีวิต)"

    if "พ้นสภาพคืนไม่ได้" in s:
        return "พ้นสภาพคืนไม่ได้"
    if "สำเร็จการศึกษา" in s:
        return "สำเร็จการศึกษา"
    if "สภาพสมบูรณ์" in s:
        return "สภาพสมบูรณ์"
    if "รักษาสภาพ" in s:
        return "รักษาสภาพนิสิต"
    if "ลาพัก" in s:
        return "ลาพักการเรียน"
    if "ลาออก" in s:
        return "ลาออก"
    if "คณบดี" in s:
        return "พ้นสภาพ (คณบดีอนุมัติ)"
    if "พ้นสภาพ" in s:
        return "พ้นสภาพ"
    if "ปัจจุบัน" in s or "กำลังศึกษา" in s:
        return "นิสิตปัจจุบัน"
    return s or "ไม่ระบุ"


def cut_plan_type(x):
    s = clean_text(x)
    if not s:
        return ""
    return re.split(
        r"\s*(?:แผน|แบบ)(?:\s|[:：\-/]|$).*$",
        s,
        maxsplit=1,
    )[0].strip(" -:：/|")


def read_excel(uploaded):
    df = pd.read_excel(uploaded, sheet_name="ข้อมูลนิสิต")
    df.columns = [clean_text(c) for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("ไม่พบคอลัมน์ที่จำเป็น: " + ", ".join(missing))
    return df


def metric_row(label, g, limit, durations):
    r = {"ปีที่เข้า": label, "จำนวนนิสิตรับเข้า(คน)": len(g)}

    for d in durations:
        r[d] = int((g["ระยะเวลา(ปี)"] == d).sum())

    # จำนวนนิสิตจบทั้งหมด = นับจากคอลัมน์ "สถานะนิสิต" โดยตรง
    # ต้องเป็นค่า "สำเร็จการศึกษา" เท่านั้น ไม่รวมสถานะอื่น
    grads = g[g["สถานะนิสิต"].map(clean_text) == "สำเร็จการศึกษา"].copy()
    valid = g[~g["สถานะกลุ่ม"].isin(STATUS_EXCLUDE)]
    valid_duration = valid["ระยะเวลา(ปี)"].dropna()

    # สถิติเดิม
    # นับเป็น "จำนวนนิสิต" โดยนับรหัสนิสิตไม่ซ้ำ
    # เพื่อไม่ให้นิสิตคนเดียวที่มีหลายรายการถูกนับซ้ำ
    if "รหัสนิสิต" in grads.columns:
        r["จำนวนนิสิตจบ_ทั้งหมด"] = grads["รหัสนิสิต"].map(clean_text).replace("", pd.NA).dropna().nunique()
        on_time = grads[grads["ระยะเวลา(ปี)"] <= limit]
        r["จำนวนนิสิตจบ_ตามหลักสูตร"] = on_time["รหัสนิสิต"].map(clean_text).replace("", pd.NA).dropna().nunique()
    else:
        r["จำนวนนิสิตจบ_ทั้งหมด"] = len(grads)
        r["จำนวนนิสิตจบ_ตามหลักสูตร"] = int(
            (grads["ระยะเวลา(ปี)"] <= limit).sum()
        )

    # สถิติ 4 ช่องใหม่
    # สูตรที่กำหนด:
    # จำนวนนิสิตที่ไม่นับสถานะ
    # = จำนวนนิสิตรับเข้า - พ้นสภาพ(เสียชีวิต) - พ้นสภาพ - ลาออก - พ้นสภาพ (คณบดีอนุมัติ)
    death_mask = g["สถานะกลุ่ม"] == "พ้นสภาพ (เสียชีวิต)"
    dropout_mask = g["สถานะกลุ่ม"] == "พ้นสภาพ"
    resign_mask = g["สถานะกลุ่ม"] == "ลาออก"
    dean_mask = g["สถานะกลุ่ม"] == "พ้นสภาพ (คณบดีอนุมัติ)"
    excluded_mask = death_mask | dropout_mask | resign_mask | dean_mask
    excluded_count = int(excluded_mask.sum())
    r["จำนวนนิสิตที่ไม่นับสถานะ"] = len(g) - excluded_count
    valid = g[~excluded_mask]
    valid_duration = valid["ระยะเวลา(ปี)"].dropna()
    r["เฉลี่ยระยะเวลาที่ใช้(ปี) ไม่นับรวมนิสิตสถานะ เสียชีวิต พ้นสภาพ ลาออก"] = (
        round(valid_duration.mean(), 2) if len(valid_duration) else 0
    )
    r["เฉลี่ยระยะเวลาที่ใช้(ปี)"] = (
        round(grads["ระยะเวลา(ปี)"].dropna().mean(), 2)
        if grads["ระยะเวลา(ปี)"].notna().any()
        else 0
    )
    r["%จบตามเวลา"] = (
        r["จำนวนนิสิตจบ_ตามหลักสูตร"] * 100 / r["จำนวนนิสิตที่ไม่นับสถานะ"]
        if r["จำนวนนิสิตที่ไม่นับสถานะ"]
        else 0
    )

    r["ยังไม่จบ_ทั้งหมด"] = len(g) - len(grads)

    # คอลัมน์ "นิสิตปัจจุบัน" ให้นับเฉพาะสถานะ
    # "นิสิตปัจจุบัน สภาพสมบูรณ์" เท่านั้น
    r["นิสิตปัจจุบัน"] = int(
        (g["สถานะนิสิต"].map(clean_text) == "นิสิตปัจจุบัน สภาพสมบูรณ์").sum()
    )

    for stt in STATUS_DISPLAY:
        if stt == "นิสิตปัจจุบัน":
            continue
        r[stt] = int((g["สถานะกลุ่ม"] == stt).sum())
    r["พ้นสภาพคืนไม่ได้"] = int(
        (g["สถานะกลุ่ม"] == "พ้นสภาพคืนไม่ได้").sum()
    )
    return r


def build_stats(df):
    work = df.copy()
    work["ระดับ"] = work["ระดับ"].map(normalize_level)
    work["สถานะกลุ่ม"] = work["สถานะนิสิต"].map(status_group)

    # ผู้ที่ไม่ใช่ผู้สำเร็จการศึกษา จะไม่มีข้อมูลปี/เทอม/วันที่จบในการคำนวณระยะเวลา
    non_graduated = work["สถานะนิสิต"].map(clean_text) != "สำเร็จการศึกษา"
    work.loc[
        non_graduated, ["ปีที่จบ", "เทอมที่จบ", "วันที่จบ"]
    ] = pd.NA

    work["ระยะเวลา(ปี)"] = work.apply(calc_duration, axis=1)
    work["สาขาสถิติ"] = work["สาขา"].map(cut_plan_type)

    durations = [x / 2 for x in range(1, 23)]
    rows = []

    levels = [x for x in ["ป.โท", "ป.เอก"] if x in work["ระดับ"].unique()]
    levels += [x for x in work["ระดับ"].unique() if x not in levels]

    for level in levels:
        g = work[work["ระดับ"] == level]
        if g.empty:
            continue

        # ป.โท 2 ปี / ป.เอก 4 ปี
        limit = 2 if level == "ป.โท" else 4
        rows.append(metric_row(level, g, limit, durations))

        years = sorted(
            pd.to_numeric(g["ปีที่เข้า"], errors="coerce").dropna().unique()
        )
        for year in years:
            gy = g[
                pd.to_numeric(g["ปีที่เข้า"], errors="coerce") == year
            ]
            rows.append(metric_row(int(year), gy, limit, durations))

            for faculty, gf in gy.groupby("คณะ", dropna=False, sort=True):
                faculty = clean_text(faculty)
                if not faculty:
                    continue

                rows.append(metric_row("คณะ" + faculty, gf, limit, durations))

                for program, gp in gf.groupby(
                    "สาขาสถิติ", dropna=False, sort=True
                ):
                    program = clean_text(program)
                    if not program:
                        continue
                    rows.append(metric_row(program, gp, limit, durations))

    # แถวล่างสุด "รวมทั้งหมด" รวมข้อมูลทุกระดับ/ทุกปี
    if rows:
        all_g = work.copy()
        total = metric_row("รวมทั้งหมด", all_g, 2, durations)

        # ผู้สำเร็จการศึกษาตามหลักสูตร: ป.โท <= 2 ปี และ ป.เอก <= 4 ปี
        grads_all = all_g[all_g["สถานะนิสิต"].map(clean_text) == "สำเร็จการศึกษา"].copy()
        if "รหัสนิสิต" in grads_all.columns:
            total["จำนวนนิสิตจบ_ทั้งหมด"] = grads_all["รหัสนิสิต"].map(clean_text).replace("", pd.NA).dropna().nunique()
            on_time = (
                ((grads_all["ระดับ"] == "ป.โท") & (grads_all["ระยะเวลา(ปี)"] <= 2))
                | ((grads_all["ระดับ"] == "ป.เอก") & (grads_all["ระยะเวลา(ปี)"] <= 4))
            )
            total["จำนวนนิสิตจบ_ตามหลักสูตร"] = grads_all.loc[on_time, "รหัสนิสิต"].map(clean_text).replace("", pd.NA).dropna().nunique()
        total["%จบตามเวลา"] = (
            total["จำนวนนิสิตจบ_ตามหลักสูตร"] * 100 / total["จำนวนนิสิตที่ไม่นับสถานะ"]
            if total["จำนวนนิสิตที่ไม่นับสถานะ"] else 0
        )
        rows.append(total)

    # 40 คอลัมน์ตรงกับ Sheet "สถิติ" เดิม
    # ใช้ชื่อภายในที่ไม่ซ้ำกันสำหรับ % เดิม เพื่อป้องกัน pyarrow/Streamlit
    columns = ["ปีที่เข้า", "จำนวนนิสิตรับเข้า(คน)"] + durations + [
        "จำนวนนิสิตจบ_ทั้งหมด",
        "จำนวนนิสิตจบ_ตามหลักสูตร",
        "%จบตามเวลา_เดิม",
        "ยังไม่จบ_ทั้งหมด",
        "นิสิตปัจจุบัน",
        "พ้นสภาพ (คณบดีอนุมัติ)",
        "พ้นสภาพ (เสียชีวิต)",
        "พ้นสภาพ",
        "รักษาสภาพนิสิต",
        "ลาพักการเรียน",
        "ลาออก",
        "เฉลี่ยระยะเวลาที่ใช้(ปี)",
        "เฉลี่ยระยะเวลาที่ใช้(ปี) ไม่นับรวมนิสิตสถานะ เสียชีวิต พ้นสภาพ ลาออก",
        "จำนวนนิสิตที่ไม่นับสถานะ เสียชีวิต พ้นสภาพ ลาออก พ้นสภาพ (คณบดีอนุมัติ)",
        "ตามระยะเวลาของหลักสูตร 2 ปี/ 4 ปี (คน)",
        "%จบตามเวลา",
    ]

    out = []
    for r in rows:
        vals = [r["ปีที่เข้า"], r["จำนวนนิสิตรับเข้า(คน)"]]
        vals += [r[d] for d in durations]
        # คอลัมน์ Y:AN
        # AL = รับเข้า - คณบดีอนุมัติ - เสียชีวิต - พ้นสภาพ - ลาออก
        # AM = จำนวนจบตามระยะเวลาหลักสูตร
        # AN = % จบตามเวลา
        excluded_count = (
            r["พ้นสภาพ (คณบดีอนุมัติ)"]
            + r["พ้นสภาพ (เสียชีวิต)"]
            + r["พ้นสภาพ"]
            + r["ลาออก"]
        )
        not_counted = r["จำนวนนิสิตรับเข้า(คน)"] - excluded_count
        on_time_count = r["จำนวนนิสิตจบ_ตามหลักสูตร"]
        on_time_pct = (
            on_time_count * 100 / not_counted
            if not_counted else 0
        )

        # บังคับค่าของ 3 คอลัมน์ท้ายให้ถูกต้องก่อนสร้าง DataFrame
        r["จำนวนนิสิตที่ไม่นับสถานะ"] = not_counted
        r["จำนวนนิสิตจบ_ตามหลักสูตร"] = on_time_count
        r["%จบตามเวลา"] = on_time_pct

        vals += [
            r["จำนวนนิสิตจบ_ทั้งหมด"],
            r["จำนวนนิสิตจบ_ตามหลักสูตร"],
            r["%จบตามเวลา"],
            r["ยังไม่จบ_ทั้งหมด"],
            r["นิสิตปัจจุบัน"],
            r["พ้นสภาพ (คณบดีอนุมัติ)"],
            r["พ้นสภาพ (เสียชีวิต)"],
            r["พ้นสภาพ"],
            r["รักษาสภาพนิสิต"],
            r["ลาพักการเรียน"],
            r["ลาออก"],
            r["เฉลี่ยระยะเวลาที่ใช้(ปี)"],
            r["เฉลี่ยระยะเวลาที่ใช้(ปี) ไม่นับรวมนิสิตสถานะ เสียชีวิต พ้นสภาพ ลาออก"],
            not_counted,
            on_time_count,
            on_time_pct,
        ]
        out.append(vals)

    return work, pd.DataFrame(out, columns=columns)


def copy_row_style(ws, source_row, target_row, max_col=40):
    if source_row == target_row:
        return

    ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height

    for c in range(1, max_col + 1):
        src = ws.cell(source_row, c)
        dst = ws.cell(target_row, c)

        if src.has_style:
            dst._style = copy(src._style)
        if src.number_format:
            dst.number_format = src.number_format
        if src.alignment:
            dst.alignment = copy(src.alignment)
        if src.font:
            dst.font = copy(src.font)
        if src.fill:
            dst.fill = copy(src.fill)
        if src.border:
            dst.border = copy(src.border)
        if src.protection:
            dst.protection = copy(src.protection)


def make_excel(original_uploaded, original, processed, stats):
    """สร้าง Sheet สถิติให้เป็น Template ตามแบบที่กำหนด พร้อมคงสี/เส้น/รูปแบบ"""
    from openpyxl import load_workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

    original_uploaded.seek(0)
    wb = load_workbook(original_uploaded)

    if "ข้อมูลประมวลผล" in wb.sheetnames:
        del wb["ข้อมูลประมวลผล"]

    ws_processed = wb.create_sheet("ข้อมูลประมวลผล")
    ws_processed.append(processed.columns.tolist())
    for row in processed.where(pd.notna(processed), None).values.tolist():
        ws_processed.append(row)

    ws_processed.freeze_panes = "A2"
    ws_processed.auto_filter.ref = ws_processed.dimensions

    if "สถิติ" in wb.sheetnames:
        ws = wb["สถิติ"]
    else:
        ws = wb.create_sheet("สถิติ")

    # ============================================================
    # TEMPLATE SHEET "สถิติ"
    # ============================================================
    gray = PatternFill(fill_type="solid", fgColor="808080")
    red_fill = PatternFill(fill_type="solid", fgColor="FF0000")
    pink_fill = PatternFill(fill_type="solid", fgColor="FF99CC")
    green_fill = PatternFill(fill_type="solid", fgColor="A9D18E")
    white_fill = PatternFill(fill_type="solid", fgColor="FFFFFF")
    blue_fill = PatternFill(fill_type="solid", fgColor="2F5597")

    white_font = Font(name="Tahoma", size=10, color="FFFFFF", bold=True)
    black_font = Font(name="Tahoma", size=10, color="000000")
    red_font = Font(name="Tahoma", size=10, color="FF0000", bold=True)
    blue_font = Font(name="Tahoma", size=10, color="FFFFFF", bold=True)

    thin = Side(style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    center = Alignment(
        horizontal="center",
        vertical="center",
        wrap_text=True,
    )

    # ยกเลิก merge เดิมเฉพาะบริเวณหัวตาราง
    for merged in list(ws.merged_cells.ranges):
        if merged.min_row <= 3 and merged.min_col <= 40:
            ws.unmerge_cells(str(merged))

    # ล้างหัวตาราง A1:AN3 แล้วสร้างโครงใหม่
    for r in range(1, 4):
        for c in range(1, 41):
            ws.cell(r, c).value = None
            ws.cell(r, c).fill = gray
            ws.cell(r, c).font = white_font
            ws.cell(r, c).alignment = center
            ws.cell(r, c).border = border

    # กลุ่มหัวตาราง
    ws.merge_cells("A1:A3")
    ws.merge_cells("B1:B3")
    ws.merge_cells("C1:X1")
    ws.merge_cells("Y1:AA1")
    ws.merge_cells("AB1:AI1")

    for col in range(3, 25):
        ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)

    for col in range(25, 28):
        ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)

    for col in range(28, 36):
        ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)

    for col in range(36, 41):
        ws.merge_cells(start_row=1, start_column=col, end_row=3, end_column=col)

    ws["A1"] = "ปีที่เข้า"
    ws["B1"] = "จำนวน\nนิสิต\nรับเข้า(คน)"
    ws["C1"] = "ระยะเวลา(ปี)"
    ws["Y1"] = "จำนวนนิสิตจบ"
    ws["AB1"] = "จำนวนนิสิตที่ยังไม่จบ"

    durations = [x / 2 for x in range(1, 23)]
    for i, value in enumerate(durations, start=3):
        ws.cell(2, i).value = value

    ws["Y2"] = "ทั้งหมด(คน)"
    ws["Z2"] = "ตาม\nระยะเวลา\nของหลักสูตร\n2 ปี/ 4 ปี\n(คน)"
    ws["AA2"] = "% จบ\nตามเวลา"

    ws["AB2"] = "ทั้งหมด"
    ws["AC2"] = "นิสิตปัจจุบัน"
    ws["AD2"] = "พ้นสภาพ (คณบดีอนุมัติ)"
    ws["AE2"] = "พ้นสภาพ (เสียชีวิต)"
    ws["AF2"] = "พ้นสภาพ"
    ws["AG2"] = "รักษาสภาพนิสิต"
    ws["AH2"] = "ลาพักการเรียน"
    ws["AI2"] = "ลาออก"

    ws["AJ1"] = "เฉลี่ย\nระยะเวลาที่ใช้(ปี)"
    ws["AK1"] = (
        "เฉลี่ยระยะเวลาที่ใช้(ปี)\n"
        "ไม่นับรวมนิสิตสถานะ\n"
        "เสียชีวิต พ้นสภาพ ลาออก"
    )
    ws["AL1"] = (
        "จำนวนนิสิตที่ไม่นับสถานะ\n"
        "เสียชีวิต พ้นสภาพ ลาออก"
    )
    ws["AM1"] = "ตาม\nระยะเวลาของหลักสูตร\n2 ปี/ 4 ปี\n(คน)"
    ws["AN1"] = "% จบ\nตามเวลา"

    # รูปแบบหัวตาราง
    for r in range(1, 4):
        for c in range(1, 41):
            cell = ws.cell(r, c)
            cell.fill = gray
            cell.font = white_font
            cell.alignment = center
            cell.border = border

    # คอลัมน์ AL ตาม Template ใช้สีน้ำเงิน
    ws["AL1"].fill = blue_fill
    ws["AL1"].font = blue_font

    # หัวข้อสถานะที่เป็นสีแดงตาม Template
    for cell_ref in ["AD2", "AE2", "AF2", "AI2"]:
        ws[cell_ref].font = red_font

    # ความกว้างคอลัมน์
    widths = {
        "A": 11, "B": 12,
        "Y": 12, "Z": 13, "AA": 10,
        "AB": 11, "AC": 12, "AD": 15, "AE": 15,
        "AF": 11, "AG": 13, "AH": 13, "AI": 10,
        "AJ": 12, "AK": 16, "AL": 15, "AM": 13, "AN": 10,
    }
    for col in range(3, 25):
        widths[chr(64 + col)] = 7
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

    ws.row_dimensions[1].height = 25
    ws.row_dimensions[2].height = 27
    ws.row_dimensions[3].height = 27

    # ============================================================
    # DATA ROWS — เริ่มที่แถว 4 ตาม Template
    # ============================================================
    first_data_row = 4
    old_last = ws.max_row

    # ล้างค่าเดิม แต่คงโครงสร้างหัวตาราง
    if old_last >= first_data_row:
        for r in range(first_data_row, old_last + 1):
            for c in range(1, 41):
                ws.cell(r, c).value = None

    # ถ้าจำนวนแถวใหม่มากกว่าเดิม ให้เพิ่มแถว
    needed_last = first_data_row + len(stats) - 1
    if needed_last > old_last:
        ws.insert_rows(old_last + 1, needed_last - old_last)

    # เขียนข้อมูล 40 คอลัมน์
    for i, (_, row) in enumerate(stats.iterrows(), start=first_data_row):
        # อ่าน 37 คอลัมน์แรกก่อน แล้วคำนวณ 3 คอลัมน์ท้ายใหม่
        # เพื่อป้องกันค่า AL:AN หายจาก DataFrame/รูปแบบคอลัมน์
        values = [
            row.iloc[j] if pd.notna(row.iloc[j]) else None
            for j in range(37)
        ]

        # AL (38) = รับเข้า - คณบดีอนุมัติ - เสียชีวิต - พ้นสภาพ - ลาออก
        not_counted = (
            (values[1] or 0)
            - (values[29] or 0)
            - (values[30] or 0)
            - (values[31] or 0)
            - (values[34] or 0)
        )
        # AM (39) = จำนวนนิสิตจบตามระยะเวลาของหลักสูตร
        on_time = values[25] or 0
        # AN (40) = % จบตามเวลา
        on_time_pct = (on_time * 100 / not_counted) if not_counted else 0
        values += [not_counted, on_time, on_time_pct]

        label = clean_text(values[0])

        if label in ("ป.โท", "ป.เอก"):
            row_fill = red_fill
        elif re.fullmatch(r"\d{4}", label):
            row_fill = white_fill
        elif label.startswith("คณะ"):
            row_fill = pink_fill
        else:
            row_fill = green_fill

        for c, value in enumerate(values, start=1):
            cell = ws.cell(i, c)
            cell.value = value
            cell.fill = row_fill
            cell.font = black_font
            cell.alignment = center
            cell.border = border

        # แถวระดับใช้ตัวหนา
        if label in ("ป.โท", "ป.เอก"):
            for c in range(1, 41):
                ws.cell(i, c).font = Font(
                    name="Tahoma",
                    size=10,
                    color="000000",
                    bold=True,
                )

        # ยืนยันการเขียน 3 คอลัมน์ท้าย AL:AN โดยอ้างอิงชื่อคอลัมน์โดยตรง
        # ไม่พึ่งตำแหน่งของ DataFrame
        ws.cell(i, 38).value = row["จำนวนนิสิตที่ไม่นับสถานะ เสียชีวิต พ้นสภาพ ลาออก พ้นสภาพ (คณบดีอนุมัติ)"]
        ws.cell(i, 39).value = row["ตามระยะเวลาของหลักสูตร 2 ปี/ 4 ปี (คน)"]
        ws.cell(i, 40).value = row["%จบตามเวลา"]

        # ตัวเลขระยะเวลาเฉลี่ยและ % แสดง 2 ตำแหน่ง
        ws.cell(i, 36).number_format = "0.00"
        ws.cell(i, 37).number_format = "0.00"
        ws.cell(i, 40).number_format = "0.00"

    # ล้างแถวที่เกินจากข้อมูลใหม่
    for r in range(needed_last + 1, old_last + 1):
        for c in range(1, 41):
            ws.cell(r, c).value = None

    ws.freeze_panes = "A4"
    ws.sheet_view.showGridLines = False

    if len(stats):
        ws.auto_filter.ref = f"A3:AN{needed_last}"

    # ============================================================
    # สร้าง Sheet "คณะ" และ "ปี" จาก Sheet "สถิติ" โดยตรง
    # ไม่คำนวณสถิติใหม่: ใช้ค่าจาก stats ที่คำนวณเสร็จแล้วทั้งหมด
    #
    # คณะ = คัดลอกสถิติ แล้วลบแถวระดับสาขาออก
    # ปี   = คัดลอกสถิติ แล้วลบแถวคณะและสาขาออก
    # ============================================================
    def write_copied_stats_sheet(sheet_name, source_stats, mode):
        if sheet_name in wb.sheetnames:
            del wb[sheet_name]

        sws = wb.copy_worksheet(ws)
        sws.title = sheet_name

        labels = source_stats["ปีที่เข้า"].map(clean_text)

        # แถวที่ต้องเก็บจาก Sheet "สถิติ"
        is_level = labels.isin(["ป.โท", "ป.เอก"])
        is_year = labels.str.match(r"^\d{4}(?:\.0)?$", na=False)
        is_faculty = labels.str.startswith("คณะ", na=False)
        is_total = labels == "รวมทั้งหมด"

        if mode == "faculty":
            # ป.โท -> ปี -> คณะ และ ป.เอก -> ปี -> คณะ
            keep = is_level | is_year | is_faculty | is_total
        else:
            # ป.โท -> ปี และ ป.เอก -> ปี
            keep = is_level | is_year | is_total

        copied = source_stats.loc[keep].copy().reset_index(drop=True)

        old_rows = sws.max_row
        # ข้อมูลของชีทสถิติเริ่มที่แถว 4 จึงต้องเขียนทับตั้งแต่แถว 4
        # เพื่อไม่ให้แถว ป.โท / ป.เอก จากชีทต้นแบบซ้ำกับข้อมูลที่คัดลอก
        for rr in range(4, old_rows + 1):
            for cc in range(1, 41):
                sws.cell(rr, cc).value = None
                # ล้างสีของแถวว่างด้านล่างทั้งหมด
                sws.cell(rr, cc).fill = PatternFill(fill_type=None)

        needed = 4 + len(copied) - 1
        if needed > old_rows:
            sws.insert_rows(old_rows + 1, needed - old_rows)

        for i, (_, row) in enumerate(copied.iterrows(), start=4):
            label = clean_text(row["ปีที่เข้า"])

            if label in ("ป.โท", "ป.เอก"):
                row_fill = red_fill
            elif re.fullmatch(r"\d{4}(?:\.0)?", label):
                row_fill = white_fill
            elif label.startswith("คณะ"):
                row_fill = pink_fill
            else:
                row_fill = green_fill

            # คัดลอกค่าทั้ง 40 คอลัมน์จาก Sheet "สถิติ" โดยตรง
            for c in range(1, 41):
                cell = sws.cell(i, c)
                value = row.iloc[c - 1]
                cell.value = value if pd.notna(value) else None

                # ช่องว่างไม่มีสีพื้น
                if value is None or pd.isna(value):
                    cell.fill = PatternFill(fill_type=None)
                else:
                    cell.fill = row_fill

                cell.font = black_font
                cell.alignment = center
                cell.border = border

            if label in ("ป.โท", "ป.เอก"):
                for c in range(1, 41):
                    sws.cell(i, c).font = Font(
                        name="Tahoma",
                        size=10,
                        color="000000",
                        bold=True,
                    )

            sws.cell(i, 36).number_format = "0.00"
            sws.cell(i, 37).number_format = "0.00"
            sws.cell(i, 40).number_format = "0.00"

        sws.freeze_panes = "A4"
        sws.sheet_view.showGridLines = False
        if len(copied):
            sws.auto_filter.ref = f"A4:AN{needed}"

    # ลบ Sheet เดิมที่แยก ป.โท / ป.เอก
    for old_sheet in ["ป.โท คณะ", "ป.โท ปี", "ป.เอก คณะ", "ป.เอก ปี", "คณะ", "ปี"]:
        if old_sheet in wb.sheetnames:
            del wb[old_sheet]

    # ใช้ข้อมูลจาก Sheet "สถิติ" โดยตรง ไม่คำนวณใหม่
    write_copied_stats_sheet("คณะ", stats, "faculty")
    write_copied_stats_sheet("ปี", stats, "year")

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out.getvalue()


st.title("📊 ระบบประมวลผลสถิตินิสิต")
st.caption("รูปแบบการทำงาน: Upload Excel → กดประมวลผล → สถิติทั้งหมดอัปเดต")

uploaded = st.file_uploader(
    "1) อัปโหลดไฟล์ Excel",
    type=["xlsx", "xls"],
    help="ไฟล์ควรมีชีตชื่อ 'ข้อมูลนิสิต'",
)

if uploaded:
    try:
        df = read_excel(uploaded)
        st.success(f"อ่านข้อมูลสำเร็จ: {len(df):,} รายการ")

        # ============================================================
        # DASHBOARD — ข้อมูลนิสิตปัจจุบัน
        # ============================================================
        # Dashboard ทั้ง 4 ตัวนับสถานะนิสิตปัจจุบัน
        # รวม: นิสิตปัจจุบัน สภาพสมบูรณ์ + รักษาสภาพ + ลาพักการเรียน
        current_statuses = {
            "นิสิตปัจจุบัน สภาพสมบูรณ์",
            "รักษาสภาพนิสิต",
            "ลาพักการเรียน",
        }
        current_df = df[
            df["สถานะนิสิต"].astype(str).str.strip().isin(current_statuses)
        ].copy()

        # ป.โท / ป.เอก นับจากคอลัมน์ "ระดับ"
        level_norm = current_df["ระดับ"].map(normalize_level)
        master_count = int((level_norm == "ป.โท").sum())
        doctoral_count = int((level_norm == "ป.เอก").sum())

        # ไทย / ต่างชาติ นับจากคอลัมน์ "ไทย-ต่างชาติ"
        thai_count = int(
            (current_df["ไทย-ต่างชาติ"].astype(str).str.strip() == "ไทย").sum()
        )
        foreign_count = int(
            (current_df["ไทย-ต่างชาติ"].astype(str).str.strip() == "ต่างชาติ").sum()
        )

        st.markdown(
            """
            <style>
            .dashboard-box {
                background: rgba(243, 247, 252, 0.94);
                padding: 18px 10px 22px 10px;
                margin-bottom: 18px;
            }
            .dashboard-number {
                color: #0b2a4a;
                font-size: 42px;
                font-weight: 700;
                text-align: center;
                line-height: 1.1;
            }
            .dashboard-label {
                color: #0b2a4a;
                font-size: 16px;
                text-align: center;
                line-height: 1.7;
                margin-top: 18px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        d1, d2, d3, d4 = st.columns(4)
        dashboard_items = [
            (master_count, "จำนวนนิสิต<br>ระดับปริญญาโท"),
            (doctoral_count, "จำนวนนิสิต<br>ระดับปริญญาเอก"),
            (thai_count, "จำนวนนิสิต<br>ไทยทั้งหมด"),
            (foreign_count, "จำนวนนิสิต<br>ต่างชาติทั้งหมด"),
        ]

        for col, (value, label) in zip((d1, d2, d3, d4), dashboard_items):
            with col:
                st.markdown(
                    f'''
                    <div class="dashboard-box">
                        <div class="dashboard-number">{value:,}</div>
                        <div class="dashboard-label">{label}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

        with st.expander("ดูตัวอย่างข้อมูลที่นำเข้า"):
            st.dataframe(df.head(20), use_container_width=True)

        if st.button(
            "🚀 2) ประมวลผลและอัปเดตสถิติ",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("กำลังประมวลผลข้อมูลและสร้างสถิติ..."):
                processed, stats = build_stats(df)
                excel_bytes = make_excel(
                    uploaded, df, processed, stats
                )

            st.session_state["processed"] = processed
            st.session_state["stats"] = stats
            st.session_state["excel_bytes"] = excel_bytes

            st.success(
                "ประมวลผลเสร็จแล้ว — สถิติอัปเดตเรียบร้อย "
                "โดยคงสีและรูปแบบของ Sheet สถิติเดิม"
            )

    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ได้: {e}")


if "stats" in st.session_state:
    stats = st.session_state["stats"]
    processed = st.session_state["processed"]

    st.subheader("ผลสถิติ")

    a, b, c, d = st.columns(4)
    a.metric("แถวสถิติ", f"{len(stats):,}")
    b.metric(
        "ผู้สำเร็จการศึกษา",
        f"{(processed['สถานะกลุ่ม'] == 'สำเร็จการศึกษา').sum():,}",
    )
    c.metric(
        "ระยะเวลาเฉลี่ย",
        f"{processed['ระยะเวลา(ปี)'].mean():.2f} ปี",
    )
    d.metric(
        "ข้อมูลที่คำนวณระยะเวลาได้",
        f"{processed['ระยะเวลา(ปี)'].notna().sum():,}",
    )

    # ป้องกัน pyarrow/Streamlit ValueError จากชื่อคอลัมน์ซ้ำ
    display_stats = stats.loc[
        :, ~stats.columns.duplicated(keep="last")
    ].copy()

    st.dataframe(
        display_stats,
        use_container_width=True,
        height=600,
    )

    st.download_button(
        "⬇️ 3) ดาวน์โหลด Excel ผลลัพธ์",
        data=st.session_state["excel_bytes"],
        file_name="สถิตินิสิต_ประมวลผลแล้ว.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )
