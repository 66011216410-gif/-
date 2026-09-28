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


def upload_processed_data(processed: pd.DataFrame):
    client = get_supabase_client()
    if client is None:
        return False, "ยังไม่ได้ตั้งค่า SUPABASE_URL / SUPABASE_KEY ใน Streamlit Secrets"

    table = "ข้อมูลประมวลผล"
    data = processed.copy()
    data = data.where(pd.notna(data), None)
    records = data.to_dict(orient="records")

    # ล้างข้อมูลเดิมก่อนนำเข้าชุดใหม่ เพื่อให้ Power BI เห็นข้อมูลชุดล่าสุดตรงกับเว็บ
    client.table(table).delete().neq("id", 0).execute()

    if records:
        for start in range(0, len(records), 500):
            client.table(table).insert(records[start:start + 500]).execute()

    return True, f"ส่งข้อมูล {len(records):,} รายการเข้า Supabase แล้ว"
