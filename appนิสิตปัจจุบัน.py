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
    /* ภาพพื้นหลังเต็มหน้าจอ */
    #building-background {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: none !important;
        max-height: none !important;
        object-fit: cover !important;
        object-position: center center !important;
        opacity: 0.24 !important;
        z-index: 9998 !important;
        pointer-events: none !important;
        display: block !important;
        visibility: visible !important;
    }

    /* ทำพื้นหลังของ Streamlit ให้โปร่งใส เพื่อให้เห็นภาพ */
    html, body,
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

    /* เนื้อหาอยู่เหนือภาพ แต่ไม่บังภาพด้วยพื้นขาว */
    section[data-testid="stMain"],
    div[data-testid="stMainBlockContainer"],
    div[data-testid="stVerticalBlock"] {
        position: relative;
        z-index: 9999;
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

st.markdown(
    '<img id="building-background" src="data:image/webp;base64,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" alt="">',
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
