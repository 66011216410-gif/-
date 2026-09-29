import os
import pandas as pd
from supabase import create_client


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        try:
            import streamlit as st
            url = url or st.secrets.get("SUPABASE_URL")
            key = key or st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass

    if not url or not key:
        return None
    return create_client(url, key)


def _json_safe(value):
    """แปลงค่าจาก pandas/numpy ให้เป็นชนิดที่ Supabase JSON รองรับ"""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


# คอลัมน์ที่สร้างไว้ใน Supabase
SUPABASE_COLUMNS = {
    "ปีที่เข้า", "ภาคการศึกษาที่เข้า", "รหัสนิสิต", "คณะ", "วิทยาเขต",
    "สาขา", "ระดับ", "รหัสสถานะนิสิต", "สถานะนิสิต", "ปีที่จบ",
    "เทอมที่จบ", "วันที่จบ", "สาขา_ตัดแผน", "สาขาตัดแผน", "สถานะกลุ่ม",
    "ระยะเวลา(ปี)", "ปีการศึกษา+", "จบตามเวลา", "ไฟล์ต้นทาง", "วันที่นำเข้า"
}


def upload_processed_excel_sheet(processed_sheet: pd.DataFrame):
    """ส่งข้อมูลจาก Sheet 'ข้อมูลประมวลผล' ของไฟล์ Excel ผลลัพธ์เข้า Supabase"""
    client = get_supabase_client()
    if client is None:
        return False, "ยังไม่ได้ตั้งค่า SUPABASE_URL / SUPABASE_KEY ใน Streamlit Secrets"

    table = "ข้อมูลประมวลผล"
    records = []

    for row in processed_sheet.to_dict(orient="records"):
        safe_row = {}
        for key, value in row.items():
            clean_key = str(key).strip()
            while clean_key.startswith("__"):
                clean_key = clean_key[1:]

            # ส่งเฉพาะคอลัมน์ที่มีใน schema ของ Supabase
            if clean_key not in SUPABASE_COLUMNS:
                continue

            safe_row[clean_key] = _json_safe(value)

        safe_row.pop("id", None)
        records.append(safe_row)

    try:
        # ล้างข้อมูลชุดเดิม แล้วนำข้อมูลจาก Sheet ผลลัพธ์ชุดล่าสุดเข้าไปแทน
        client.table(table).delete().neq("id", 0).execute()

        for start in range(0, len(records), 500):
            client.table(table).insert(records[start:start + 500]).execute()

        return True, f"ส่ง Sheet ข้อมูลประมวลผล {len(records):,} รายการเข้า Supabase แล้ว"
    except Exception as e:
        return False, str(e)


# รองรับโค้ดเดิมที่เรียกชื่อฟังก์ชันนี้
upload_processed_data = upload_processed_excel_sheet
