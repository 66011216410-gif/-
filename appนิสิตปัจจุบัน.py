import io
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="ระบบสถิตินิสิตบัณฑิตศึกษา", page_icon="📊", layout="wide")
REQUIRED_COLUMNS = ["ปีที่เข้า", "ภาคการศึกษาที่เข้า", "รหัสนิสิต", "คณะ", "วิทยาเขต", "สาขา", "ระดับ", "รหัสสถานะนิสิต", "สถานะนิสิต", "ปีที่จบ", "เทอมที่จบ", "วันที่จบ"]
STATUS_EXCLUDE = ["เสียชีวิต", "พ้นสภาพคืนไม่ได้", "ลาออก"]


def clean_text(x):
    if pd.isna(x): return ""
    return str(x).strip()


def num(x):
    try: return float(x)
    except Exception: return None


def calc_duration(row):
    """1 เทอม = 0.5 ปี; ภาคเดียวกันของปีเดียวกัน = 0.5 ปี"""
    y0, s0 = num(row.get("ปีที่เข้า")), num(row.get("ภาคการศึกษาที่เข้า"))
    y1, s1 = num(row.get("ปีที่จบ")), num(row.get("เทอมที่จบ"))
    if None in (y0, s0, y1, s1): return None
    semesters = (y1 - y0) * 2 + (s1 - s0) + 1
    d = semesters * 0.5
    return round(d, 1) if d > 0 else None


def normalize_level(x):
    x = clean_text(x)
    if "เอก" in x: return "ป.เอก"
    if "โท" in x: return "ป.โท"
    return x or "ไม่ระบุ"


def status_group(x):
    s = clean_text(x)
    if "สำเร็จการศึกษา" in s: return "สำเร็จการศึกษา"
    if "สภาพสมบูรณ์" in s: return "สภาพสมบูรณ์"
    if "รักษาสภาพ" in s: return "รักษาสภาพนิสิต"
    if "ลาพัก" in s: return "ลาพักการเรียน"
    if "ลาออก" in s: return "ลาออก"
    if "เสียชีวิต" in s: return "พ้นสภาพ (เสียชีวิต)"
    if "พ้นสภาพคืนไม่ได้" in s: return "พ้นสภาพคืนไม่ได้"
    if "พ้นสภาพ" in s: return "พ้นสภาพ"
    if "ปัจจุบัน" in s or "กำลังศึกษา" in s: return "นิสิตปัจจุบัน"
    return s or "ไม่ระบุ"


def cut_plan_type(x):
    s = clean_text(x)
    if not s: return ""
    return re.split(r"\s*(?:แผน|แบบ)(?:\s|[:：\-/]|$).*$", s, maxsplit=1)[0].strip(" -:：/|")


def read_excel(uploaded):
    df = pd.read_excel(uploaded, sheet_name="ข้อมูลนิสิต")
    df.columns = [clean_text(c) for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing: raise ValueError("ไม่พบคอลัมน์ที่จำเป็น: " + ", ".join(missing))
    return df


def metric_row(label, g, limit, durations):
    r = {"ปีที่เข้า": label, "จำนวนนิสิตรับเข้า(คน)": len(g)}
    for d in durations:
        r[d] = int((g["ระยะเวลา(ปี)"] == d).sum())

    grads = g[g["สถานะกลุ่ม"] == "สำเร็จการศึกษา"]
    r["จำนวนนิสิตจบ_ทั้งหมด"] = len(grads)
    r["จำนวนนิสิตจบ_ตามหลักสูตร"] = int((grads["ระยะเวลา(ปี)"] <= limit).sum())

    # กลุ่มสำหรับสถิติชุดนี้: ไม่นับ เสียชีวิต / พ้นสภาพคืนไม่ได้ / ลาออก
    valid_status = ~g["สถานะกลุ่ม"].isin(STATUS_EXCLUDE)
    valid = g[valid_status]
    r["จำนวนนิสิตที่ไม่นับสถานะ"] = len(valid)

    # เฉลี่ยระยะเวลา: ใช้เฉพาะรายการที่คำนวณระยะเวลาได้ และไม่นับ 3 สถานะที่กำหนด
    valid_duration = valid["ระยะเวลา(ปี)"].dropna()
    r["เฉลี่ยระยะเวลาที่ใช้(ปี) ไม่นับรวมนิสิตสถานะ เสียชีวิต พ้นสภาพคืนไม่ได้ ลาออก"] = (
        round(valid_duration.mean(), 2) if len(valid_duration) else 0
    )

    # % จบตามเวลา = จบภายในเกณฑ์ / จำนวนนิสิตที่ไม่นับ 3 สถานะ
    r["%จบตามเวลา"] = (
        r["จำนวนนิสิตจบ_ตามหลักสูตร"] * 100 / r["จำนวนนิสิตที่ไม่นับสถานะ"]
        if r["จำนวนนิสิตที่ไม่นับสถานะ"] else 0
    )

    r["ยังไม่จบ_ทั้งหมด"] = len(g) - len(grads)
    for stt in ["นิสิตปัจจุบัน", "สภาพสมบูรณ์", "พ้นสภาพ", "พ้นสภาพ (เสียชีวิต)", "พ้นสภาพคืนไม่ได้", "รักษาสภาพนิสิต", "ลาพักการเรียน", "ลาออก"]:
        r[stt] = int((g["สถานะกลุ่ม"] == stt).sum())
    return r


def build_stats(df):
    work = df.copy()
    work["ระดับ"] = work["ระดับ"].map(normalize_level)
    work["สถานะกลุ่ม"] = work["สถานะนิสิต"].map(status_group)

    # ถ้าไม่ใช่ผู้สำเร็จการศึกษา ให้ล้างข้อมูลปี/เทอม/วันที่จบก่อนคำนวณระยะเวลา
    non_graduated = work["สถานะนิสิต"].map(clean_text) != "สำเร็จการศึกษา"
    work.loc[non_graduated, ["ปีที่จบ", "เทอมที่จบ", "วันที่จบ"]] = pd.NA
    work["ระยะเวลา(ปี)"] = work.apply(calc_duration, axis=1)
    work["สาขาสถิติ"] = work["สาขา"].map(cut_plan_type)

    durations = [x / 2 for x in range(1, 23)]
    rows = []
    levels = [x for x in ["ป.โท", "ป.เอก"] if x in work["ระดับ"].unique()]
    levels += [x for x in work["ระดับ"].unique() if x not in levels]

    for level in levels:
        g = work[work["ระดับ"] == level]
        if g.empty: continue

        # เกณฑ์ตามระยะเวลาหลักสูตร: ป.โท 2 ปี / ป.เอก 3 ปี
        limit = 2 if level == "ป.โท" else 3
        rows.append(metric_row(level, g, limit, durations))

        years = sorted(pd.to_numeric(g["ปีที่เข้า"], errors="coerce").dropna().unique())
        for year in years:
            gy = g[pd.to_numeric(g["ปีที่เข้า"], errors="coerce") == year]
            rows.append(metric_row(int(year), gy, limit, durations))

            for faculty, gf in gy.groupby("คณะ", dropna=False, sort=True):
                faculty = clean_text(faculty)
                if not faculty: continue
                rows.append(metric_row("คณะ: " + faculty, gf, limit, durations))

                for program, gp in gf.groupby("สาขาสถิติ", dropna=False, sort=True):
                    program = clean_text(program)
                    if not program: continue
                    rows.append(metric_row("  └ " + program, gp, limit, durations))

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
