# Supabase integration patch for `appนิสิตปัจจุบัน.py`

ไฟล์นี้เป็น patch แยกเพื่อความปลอดภัย ยังไม่แทนที่ไฟล์หลักโดยอัตโนมัติ

## 1. เพิ่ม import ด้านบนของ `appนิสิตปัจจุบัน.py`

```python
from supabase_sync import sync_to_supabase
```

## 2. ในปุ่ม `🚀 2) ประมวลผลและอัปเดตสถิติ`

ค้นหาบรรทัด:

```python
processed, stats = build_stats(df)
excel_bytes = make_excel(uploaded_files[0], df, processed, stats)
```

เปลี่ยนเป็น:

```python
processed, stats = build_stats(df)

# ส่งข้อมูลประมวลผลล่าสุดเข้า Supabase
try:
    synced_count = sync_to_supabase(processed)
    st.session_state["supabase_synced_count"] = synced_count
except Exception as supabase_error:
    st.session_state["supabase_sync_error"] = str(supabase_error)

excel_bytes = make_excel(uploaded_files[0], df, processed, stats)
```

## 3. แสดงผลสถานะการส่ง Supabase หลังประมวลผล

ใส่ต่อจาก `st.success("ประมวลผลเสร็จแล้ว ...")`:

```python
if st.session_state.get("supabase_sync_error"):
    st.warning(
        "ประมวลผลสำเร็จ แต่ยังส่งข้อมูลเข้า Supabase ไม่ได้: "
        + st.session_state["supabase_sync_error"]
    )
elif "supabase_synced_count" in st.session_state:
    st.info(
        f"ส่งข้อมูลเข้า Supabase แล้ว {st.session_state['supabase_synced_count']:,} รายการ"
    )
```

## 4. Streamlit Secrets

ตั้งค่าใน Streamlit Cloud → Settings → Secrets:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_SECRET_KEY"
```

ห้ามใส่ Secret key ลง GitHub

## 5. ไฟล์ที่มีอยู่แล้ว

`supabase_sync.py` เป็นตัวส่ง DataFrame ไปยังตาราง Supabase `ข้อมูลประมวลผล`

`requirements.txt` มี dependency `supabase` แล้ว

## 6. หลังแก้

ลำดับการทำงานจะเป็น:

Excel หลายไฟล์ → ประมวลผล → สร้าง `ปีการศึกษา+` → ส่ง `processed` เข้า Supabase → ดาวน์โหลด Excel
