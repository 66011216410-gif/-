import io
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ระบบสถิตินิสิตบัณฑิตศึกษา",
    page_icon="📊",
    layout="wide",
)

REQUIRED_COLUMNS = [
    "ปีที่เข้า", "ภาคการศึกษาที่เข้า", "รหัสนิสิต", "คณะ", "วิทยาเขต",
    "สาขา", "ระดับ", "รหัสสถานะนิสิต", "สถานะนิสิต", "ปีที่จบ",
    "เทอมที่จบ", "วันที่จบ"
]

STATUS_EXCLUDE = ["เสียชีวิต", "พ้นสภาพคืนไม่ได้", "ลาออก"]

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
    """คำนวณระยะเวลาเป็นช่วง 0.5 ปีจากภาคที่เข้า -> ภาคที่จบ"""
    y0, s0 = num(row.get("ปีที่เข้า")), num(row.get("ภาคการศึกษาที่เข้า"))
    y1, s1 = num(row.get("ปีที่จบ")), num(row.get("เทอมที่จบ"))
    if None in (y0, s0, y1, s1):
        return None
    d = (y1 - y0) + (s1 - s0) * 0.5
    return round(d, 1) if d >= 0 else None

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
    if "รักษาสภาพ" in s:
        return "รักษาสภาพนิสิต"
    if "ลาพัก" in s:
        return "ลาพักการเรียน"
    if "ลาออก" in s:
        return "ลาออก"
    if "เสียชีวิต" in s:
        return "พ้นสภาพ (เสียชีวิต)"
    if "พ้นสภาพ" in s:
        return "พ้นสภาพ"
    if "ปัจจุบัน" in s or "กำลังศึกษา" in s:
        return "นิสิตปัจจุบัน"
    return s or "ไม่ระบุ"

def read_excel(uploaded):
    df = pd.read_excel(uploaded, sheet_name="ข้อมูลนิสิต")
    df.columns = [clean_text(c) for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("ไม่พบคอลัมน์ที่จำเป็น: " + ", ".join(missing))
    return df

def build_stats(df):
    work = df.copy()
    work["ระดับ"] = work["ระดับ"].map(normalize_level)
    work["สถานะกลุ่ม"] = work["สถานะนิสิต"].map(status_group)

    # กฎข้อมูลจบ: เฉพาะผู้ที่มีสถานะ "สำเร็จการศึกษา" เท่านั้น
    # ที่จะเก็บ ปีที่จบ / เทอมที่จบ / วันที่จบ
    non_graduated = work["สถานะนิสิต"].map(clean_text) != "สำเร็จการศึกษา"
    work.loc[non_graduated, ["ปีที่จบ", "เทอมที่จบ", "วันที่จบ"]] = pd.NA

    work["ระยะเวลา(ปี)"] = work.apply(calc_duration, axis=1)

    durations = [x / 2 for x in range(1, 23)]
    rows = []
    levels = [x for x in ["ป.โท", "ป.เอก"] if x in work["ระดับ"].unique()]
    levels += [x for x in work["ระดับ"].unique() if x not in levels]

    for level in levels:
        g = work[work["ระดับ"] == level]
        if g.empty:
            continue
        r = {"ปีที่เข้า": level, "จำนวนนิสิตรับเข้า(คน)": len(g)}
        for d in durations:
            r[d] = int((g["ระยะเวลา(ปี)"] == d).sum())
        grads = g[g["สถานะกลุ่ม"] == "สำเร็จการศึกษา"]
        r["จำนวนนิสิตจบ_ทั้งหมด"] = len(grads)
        limit = 2 if level == "ป.โท" else 4
        r["จำนวนนิสิตจบ_ตามหลักสูตร"] = int((grads["ระยะเวลา(ปี)"] <= limit).sum())
        r["%จบตามเวลา"] = r["จำนวนนิสิตจบ_ตามหลักสูตร"] * 100 / len(g) if len(g) else 0
        r["ยังไม่จบ_ทั้งหมด"] = len(g) - len(grads)
        for stt in ["นิสิตปัจจุบัน", "พ้นสภาพ", "พ้นสภาพ (เสียชีวิต)", "รักษาสภาพนิสิต", "ลาพักการเรียน", "ลาออก"]:
            r[stt] = int((g["สถานะกลุ่ม"] == stt).sum())
        valid = g[~g["สถานะกลุ่ม"].isin(STATUS_EXCLUDE)]
        r["เฉลี่ยระยะเวลา(ปี)"] = valid["ระยะเวลา(ปี)"].dropna().mean() if len(valid) else 0
        rows.append(r)

        years = sorted(pd.to_numeric(g["ปีที่เข้า"], errors="coerce").dropna().unique())
        for year in years:
            gy = g[pd.to_numeric(g["ปีที่เข้า"], errors="coerce") == year]
            r = {"ปีที่เข้า": int(year), "จำนวนนิสิตรับเข้า(คน)": len(gy)}
            for d in durations:
                r[d] = int((gy["ระยะเวลา(ปี)"] == d).sum())
            grads = gy[gy["สถานะกลุ่ม"] == "สำเร็จการศึกษา"]
            r["จำนวนนิสิตจบ_ทั้งหมด"] = len(grads)
            r["จำนวนนิสิตจบ_ตามหลักสูตร"] = int((grads["ระยะเวลา(ปี)"] <= limit).sum())
            r["%จบตามเวลา"] = r["จำนวนนิสิตจบ_ตามหลักสูตร"] * 100 / len(gy) if len(gy) else 0
            r["ยังไม่จบ_ทั้งหมด"] = len(gy) - len(grads)
            for stt in ["นิสิตปัจจุบัน", "พ้นสภาพ", "พ้นสภาพ (เสียชีวิต)", "รักษาสภาพนิสิต", "ลาพักการเรียน", "ลาออก"]:
                r[stt] = int((gy["สถานะกลุ่ม"] == stt).sum())
            valid = gy[~gy["สถานะกลุ่ม"].isin(STATUS_EXCLUDE)]
            r["เฉลี่ยระยะเวลา(ปี)"] = valid["ระยะเวลา(ปี)"].dropna().mean() if len(valid) else 0
            rows.append(r)

            for faculty, gf in gy.groupby("คณะ", dropna=False, sort=True):
                faculty = clean_text(faculty)
                if not faculty:
                    continue
                r = {"ปีที่เข้า": "คณะ: " + faculty, "จำนวนนิสิตรับเข้า(คน)": len(gf)}
                for d in durations:
                    r[d] = int((gf["ระยะเวลา(ปี)"] == d).sum())
                gr = gf[gf["สถานะกลุ่ม"] == "สำเร็จการศึกษา"]
                r["จำนวนนิสิตจบ_ทั้งหมด"] = len(gr)
                r["จำนวนนิสิตจบ_ตามหลักสูตร"] = int((gr["ระยะเวลา(ปี)"] <= limit).sum())
                r["%จบตามเวลา"] = r["จำนวนนิสิตจบ_ตามหลักสูตร"] * 100 / len(gf) if len(gf) else 0
                r["ยังไม่จบ_ทั้งหมด"] = len(gf) - len(gr)
                for stt in ["นิสิตปัจจุบัน", "พ้นสภาพ", "พ้นสภาพ (เสียชีวิต)", "รักษาสภาพนิสิต", "ลาพักการเรียน", "ลาออก"]:
                    r[stt] = int((gf["สถานะกลุ่ม"] == stt).sum())
                valid = gf[~gf["สถานะกลุ่ม"].isin(STATUS_EXCLUDE)]
                r["เฉลี่ยระยะเวลา(ปี)"] = valid["ระยะเวลา(ปี)"].dropna().mean() if len(valid) else 0
                rows.append(r)

                for program, gp in gf.groupby("สาขา", dropna=False, sort=True):
                    program = clean_text(program)
                    if not program:
                        continue
                    r = {"ปีที่เข้า": "  └ " + program, "จำนวนนิสิตรับเข้า(คน)": len(gp)}
                    for d in durations:
                        r[d] = int((gp["ระยะเวลา(ปี)"] == d).sum())
                    gr = gp[gp["สถานะกลุ่ม"] == "สำเร็จการศึกษา"]
                    r["จำนวนนิสิตจบ_ทั้งหมด"] = len(gr)
                    r["จำนวนนิสิตจบ_ตามหลักสูตร"] = int((gr["ระยะเวลา(ปี)"] <= limit).sum())
                    r["%จบตามเวลา"] = r["จำนวนนิสิตจบ_ตามหลักสูตร"] * 100 / len(gp) if len(gp) else 0
                    r["ยังไม่จบ_ทั้งหมด"] = len(gp) - len(gr)
                    for stt in ["นิสิตปัจจุบัน", "พ้นสภาพ", "พ้นสภาพ (เสียชีวิต)", "รักษาสภาพนิสิต", "ลาพักการเรียน", "ลาออก"]:
                        r[stt] = int((gp["สถานะกลุ่ม"] == stt).sum())
                    valid = gp[~gp["สถานะกลุ่ม"].isin(STATUS_EXCLUDE)]
                    r["เฉลี่ยระยะเวลา(ปี)"] = valid["ระยะเวลา(ปี)"].dropna().mean() if len(valid) else 0
                    rows.append(r)

    return work, pd.DataFrame(rows)

def make_excel(original, processed, stats):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        original.to_excel(writer, sheet_name="ข้อมูลนิสิต", index=False)
        processed.to_excel(writer, sheet_name="ข้อมูลประมวลผล", index=False)
        stats.to_excel(writer, sheet_name="สถิติ", index=False)
        for sheet in ["ข้อมูลนิสิต", "ข้อมูลประมวลผล", "สถิติ"]:
            ws = writer.book[sheet]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                max_len = max(len(str(c.value or "")) for c in col[:200]) + 2
                ws.column_dimensions[col[0].column_letter].width = min(max(max_len, 10), 40)
    out.seek(0)
    return out.getvalue()

st.title("📊 ระบบประมวลผลสถิตินิสิต")
st.caption("รูปแบบการทำงาน: Upload Excel → กดประมวลผล → สถิติทั้งหมดอัปเดต")

uploaded = st.file_uploader("1) อัปโหลดไฟล์ Excel", type=["xlsx", "xls"], help="ไฟล์ควรมีชีตชื่อ 'ข้อมูลนิสิต'")

if uploaded:
    try:
        df = read_excel(uploaded)
        st.success(f"อ่านข้อมูลสำเร็จ: {len(df):,} รายการ")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("นิสิตทั้งหมด", f"{len(df):,}")
        c2.metric("ป.โท", f"{(df['ระดับ'].map(normalize_level) == 'ป.โท').sum():,}")
        c3.metric("ป.เอก", f"{(df['ระดับ'].map(normalize_level) == 'ป.เอก').sum():,}")
        c4.metric("ปีที่เข้า", f"{df['ปีที่เข้า'].nunique():,}")
        with st.expander("ดูตัวอย่างข้อมูลที่นำเข้า"):
            st.dataframe(df.head(20), use_container_width=True)
        if st.button("🚀 2) ประมวลผลและอัปเดตสถิติ", type="primary", use_container_width=True):
            with st.spinner("กำลังประมวลผลข้อมูลและสร้างสถิติ..."):
                processed, stats = build_stats(df)
                excel_bytes = make_excel(df, processed, stats)
            st.session_state["processed"] = processed
            st.session_state["stats"] = stats
            st.session_state["excel_bytes"] = excel_bytes
            st.success("ประมวลผลเสร็จแล้ว — สถิติอัปเดตเรียบร้อย")
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ได้: {e}")

if "stats" in st.session_state:
    stats = st.session_state["stats"]
    processed = st.session_state["processed"]
    st.subheader("ผลสถิติ")
    a, b, c, d = st.columns(4)
    a.metric("แถวสถิติ", f"{len(stats):,}")
    b.metric("ผู้สำเร็จการศึกษา", f"{(processed['สถานะกลุ่ม'] == 'สำเร็จการศึกษา').sum():,}")
    c.metric("ระยะเวลาเฉลี่ย", f"{processed['ระยะเวลา(ปี)'].mean():.2f} ปี")
    d.metric("ข้อมูลที่คำนวณระยะเวลาได้", f"{processed['ระยะเวลา(ปี)'].notna().sum():,}")
    st.dataframe(stats, use_container_width=True, height=600)
    st.download_button("⬇️ 3) ดาวน์โหลด Excel ผลลัพธ์", data=st.session_state["excel_bytes"], file_name="สถิตินิสิต_ประมวลผลแล้ว.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
