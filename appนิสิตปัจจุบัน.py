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
STATUS_EXCLUDE = ["พ้นสภาพ (เสียชีวิต)", "พ้นสภาพคืนไม่ได้", "ลาออก"]

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
    if "เสียชีวิต" in s:
        return "พ้นสภาพ (เสียชีวิต)"
    if "พ้นสภาพคืนไม่ได้" in s:
        return "พ้นสภาพคืนไม่ได้"
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

    grads = g[g["สถานะกลุ่ม"] == "สำเร็จการศึกษา"]
    valid = g[~g["สถานะกลุ่ม"].isin(STATUS_EXCLUDE)]
    valid_duration = valid["ระยะเวลา(ปี)"].dropna()

    # สถิติเดิม
    r["จำนวนนิสิตจบ_ทั้งหมด"] = len(grads)
    r["จำนวนนิสิตจบ_ตามหลักสูตร"] = int(
        (grads["ระยะเวลา(ปี)"] <= limit).sum()
    )

    # สถิติ 4 ช่องใหม่
    r["จำนวนนิสิตที่ไม่นับสถานะ"] = len(valid)
    r["เฉลี่ยระยะเวลาที่ใช้(ปี) ไม่นับรวมนิสิตสถานะ เสียชีวิต พ้นสภาพคืนไม่ได้ ลาออก"] = (
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
    for stt in STATUS_DISPLAY:
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
        "เฉลี่ยระยะเวลาที่ใช้(ปี) ไม่นับรวมนิสิตสถานะ เสียชีวิต พ้นสภาพคืนไม่ได้ ลาออก",
        "จำนวนนิสิตที่ไม่นับสถานะ เสียชีวิต พ้นสภาพคืนไม่ได้ ลาออก",
        "ตามระยะเวลาของหลักสูตร 2 ปี/ 4 ปี (คน)",
        "%จบตามเวลา",
    ]

    out = []
    for r in rows:
        vals = [r["ปีที่เข้า"], r["จำนวนนิสิตรับเข้า(คน)"]]
        vals += [r[d] for d in durations]
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
            r["เฉลี่ยระยะเวลาที่ใช้(ปี) ไม่นับรวมนิสิตสถานะ เสียชีวิต พ้นสภาพคืนไม่ได้ ลาออก"],
            r["จำนวนนิสิตที่ไม่นับสถานะ"],
            r["จำนวนนิสิตจบ_ตามหลักสูตร"],
            r["%จบตามเวลา"],
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
        "เสียชีวิต พ้นสภาพคืนไม่ได้ ลาออก"
    )
    ws["AL1"] = (
        "จำนวนนิสิตที่ไม่นับสถานะ\n"
        "เสียชีวิต พ้นสภาพคืนไม่ได้"
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
        values = [
            row.iloc[j] if pd.notna(row.iloc[j]) else None
            for j in range(40)
        ]

        label = clean_text(values[0])

        if label in ("ป.โท", "ป.เอก"):
            row_fill = red_fill
        elif re.fullmatch(r"\\d{4}", label):
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

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("นิสิตทั้งหมด", f"{len(df):,}")
        c2.metric(
            "ป.โท",
            f"{(df['ระดับ'].map(normalize_level) == 'ป.โท').sum():,}",
        )
        c3.metric(
            "ป.เอก",
            f"{(df['ระดับ'].map(normalize_level) == 'ป.เอก').sum():,}",
        )
        c4.metric("ปีที่เข้า", f"{df['ปีที่เข้า'].nunique():,}")

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
