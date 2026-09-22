import io
import re
from copy import copy

import pandas as pd
import streamlit as st

st.set_page_config(page_title="ระบบสถิตินิสิตบัณฑิตศึกษา", page_icon="📊", layout="wide")

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
            /* พื้นหลังเว็บจากภาพอาคารแบบจาง ๆ */
            .stApp {
                background-image:
                    linear-gradient(rgba(255, 255, 255, 0.90), rgba(255, 255, 255, 0.90)),
                    url("data:image/webp;base64,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");
                background-size: cover;
                background-position: center top;
                background-attachment: fixed;
            }
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
