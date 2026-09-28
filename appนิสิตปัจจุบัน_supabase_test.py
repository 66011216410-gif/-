import os
import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="ทดสอบ Supabase", page_icon="🧪")
st.title("🧪 ทดสอบการเชื่อมต่อ Supabase")
st.write("ไฟล์นี้ใช้ทดสอบการเชื่อมต่อเท่านั้น ยังไม่แก้ไฟล์เว็บหลัก")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error("ยังไม่พบ SUPABASE_URL หรือ SUPABASE_KEY ใน Streamlit Secrets")
        st.code('SUPABASE_URL = "https://xxxx.supabase.co"\nSUPABASE_KEY = "sb_secret_..."')
        st.stop()

try:
    supabase = create_client(url, key)
    st.success("เชื่อมต่อ Supabase สำเร็จ")
except Exception as e:
    st.error(f"เชื่อมต่อ Supabase ไม่สำเร็จ: {e}")
    st.stop()

st.subheader("1. ตรวจสอบตาราง")
if st.button("🔎 ตรวจสอบตาราง ข้อมูลประมวลผล"):
    try:
        result = supabase.table("ข้อมูลประมวลผล").select("id").limit(5).execute()
        st.success("พบตาราง ข้อมูลประมวลผล และสามารถอ่านข้อมูลได้")
        st.write(f"ตัวอย่างข้อมูลที่อ่านได้: {len(result.data)} รายการ")
    except Exception as e:
        st.error(f"อ่านตารางไม่สำเร็จ: {e}")

st.subheader("2. ทดสอบเขียนข้อมูล")
st.warning("ปุ่มนี้จะเพิ่มข้อมูลทดสอบ 1 แถวลงใน Supabase")

if st.button("🧪 เพิ่มข้อมูลทดสอบ"):
    test_row = {
        "ปีที่เข้า": "2567",
        "ภาคการศึกษาที่เข้า": "1",
        "รหัสนิสิต": "TEST_SUPABASE_001",
        "คณะ": "ข้อมูลทดสอบ",
        "วิทยาเขต": "ทดสอบ",
        "สาขา": "ทดสอบ Supabase",
        "ระดับ": "ป.โท",
        "รหัสสถานะนิสิต": "TEST",
        "สถานะนิสิต": "ข้อมูลทดสอบ",
        "ปีที่จบ": "",
        "เทอมที่จบ": "",
        "วันที่จบ": "",
        "สาขา_ตัดแผน": "ทดสอบ Supabase",
        "สถานะกลุ่ม": "ทดสอบ",
        "ระยะเวลา(ปี)": None,
        "ปีการศึกษา+": "2568",
        "ไฟล์ต้นทาง": "SUPABASE_TEST"
    }
    try:
        result = supabase.table("ข้อมูลประมวลผล").insert(test_row).execute()
        st.success("ส่งข้อมูลทดสอบเข้า Supabase สำเร็จ ✅")
        st.dataframe(pd.DataFrame(result.data), use_container_width=True)
    except Exception as e:
        st.error(f"ส่งข้อมูลทดสอบไม่สำเร็จ: {e}")

st.subheader("3. ลบข้อมูลทดสอบ")
if st.button("🗑️ ลบ TEST_SUPABASE_001"):
    try:
        result = supabase.table("ข้อมูลประมวลผล").delete().eq("รหัสนิสิต", "TEST_SUPABASE_001").execute()
        st.success("ลบข้อมูลทดสอบแล้ว")
    except Exception as e:
        st.error(f"ลบข้อมูลทดสอบไม่สำเร็จ: {e}")
