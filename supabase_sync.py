import os
import pandas as pd
from supabase import create_client


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    # Streamlit Cloud: อ่านจาก Secrets หากไม่ได้ตั้งเป็น environment variable
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
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def upload_processed_data(processed: pd.DataFrame):
    client = get_supabase_client()
    if client is None:
        return False, "ยังไม่ได้ตั้งค่า SUPABASE_URL / SUPABASE_KEY ใน Streamlit Secrets"

    table = "ข้อมูลประมวลผล"
    data = processed.copy()

    # แปลงค่าจาก pandas เช่น Timestamp / numpy scalar / NaN
    # ให้เป็นชนิด JSON ที่ Supabase รับได้
    records = []
    for row in data.to_dict(orient="records"):
        safe_row = {str(k): _json_safe(v) for k, v in row.items()}
        # id เป็น identity ให้ Supabase สร้างเอง
        safe_row.pop("id", None)
        records.append(safe_row)

    # ล้างข้อมูลเดิมก่อนนำเข้าชุดใหม่ เพื่อให้ Power BI เห็นข้อมูลชุดล่าสุดตรงกับเว็บ
    client.table(table).delete().neq("id", 0).execute()

    if records:
        for start in range(0, len(records), 500):
            client.table(table).insert(records[start:start + 500]).execute()

    return True, f"ส่งข้อมูล {len(records):,} รายการเข้า Supabase แล้ว"
