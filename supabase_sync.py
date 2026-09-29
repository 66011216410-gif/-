import os
from datetime import date, datetime, time

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
    """แปลงค่าจาก Excel/pandas/numpy/Python ให้ Supabase JSON รองรับ"""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, (pd.Timestamp, datetime, date, time)):
        return value.isoformat()

    if isinstance(value, pd.Timedelta):
        return str(value)

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, (pd.Timestamp, datetime, date, time)):
        return value.isoformat()

    return value


SUPABASE_COLUMNS = [
    "ปีที่เข้า", "ภาคการศึกษาที่เข้า", "รหัสนิสิต", "คำนำหน้า", "ชื่อ", "สกุล",
    "คณะ", "วิทยาเขต", "สาขา", "รหัสระดับ", "ระดับ", "ระบบ",
    "ยอดตั้งหน้า", "ยอดหนี้คงเหลือ", "สถานะการชำระเงิน", "สถานะการรายงานตัว",
    "รหัสสัญชาติ", "สัญชาติ(th)", "สัญชาติ(eng)", "ไทย-ต่างชาติ",
    "รหัสสถานะนิสิต", "สถานะนิสิต", "ปีที่จบ", "เทอมที่จบ", "วันที่จบ",
    "ไฟล์ต้นทาง", "ปีการศึกษา+", "สถานะกลุ่ม", "ระยะเวลา(ปี)", "จบตามเวลา",
    "สาขาสถิติ"
]


def upload_processed_excel_sheet(processed_sheet: pd.DataFrame):
    """ส่ง Sheet ข้อมูลประมวลผลเข้า Supabase โดยชุดใหม่จะแทนที่ชุดเก่าทั้งหมด"""
    client = get_supabase_client()
    if client is None:
        return False, "ยังไม่ได้ตั้งค่า SUPABASE_URL / SUPABASE_KEY ใน Streamlit Secrets"

    if processed_sheet is None or processed_sheet.empty:
        return False, "Sheet ข้อมูลประมวลผลไม่มีข้อมูล จึงไม่ลบหรือเปลี่ยนข้อมูลเดิมใน Supabase"

    df = processed_sheet.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Excel อาจใช้ __ไฟล์ต้นทาง แต่ Supabase ใช้ ไฟล์ต้นทาง
    if "__ไฟล์ต้นทาง" in df.columns and "ไฟล์ต้นทาง" not in df.columns:
        df = df.rename(columns={"__ไฟล์ต้นทาง": "ไฟล์ต้นทาง"})

    missing = [c for c in SUPABASE_COLUMNS if c not in df.columns]
    if missing:
        return False, "Sheet ข้อมูลประมวลผลขาดคอลัมน์: " + ", ".join(missing)

    df = df[SUPABASE_COLUMNS]

    records = []
    for row in df.to_dict(orient="records"):
        records.append({key: _json_safe(value) for key, value in row.items()})

    if not records:
        return False, "ไม่พบรายการข้อมูลสำหรับส่งเข้า Supabase"

    table = "ข้อมูลประมวลผล"

    try:
        # สำคัญ: ข้อมูลใหม่จะแทนที่ข้อมูลเก่าทั้งหมด
        # ลบก่อน INSERT เพื่อไม่ให้ข้อมูลจากรอบก่อนค้างอยู่
        client.table(table).delete().gte("id", 0).execute()

        inserted = 0
        for start in range(0, len(records), 500):
            batch = records[start:start + 500]
            response = client.table(table).insert(batch).execute()
            if response.data is not None:
                inserted += len(response.data)

        if inserted != len(records):
            return False, (
                f"ส่งข้อมูลไม่ครบ: Excel มี {len(records):,} แถว "
                f"แต่ Supabase ยืนยัน {inserted:,} แถว"
            )

        check = client.table(table).select("id", count="exact").limit(1).execute()
        total = getattr(check, "count", None)
        if total is not None and total != len(records):
            return False, (
                f"ตรวจสอบหลังส่งไม่ตรงกัน: ควรมี {len(records):,} แถว "
                f"แต่พบ {total:,} แถว"
            )

        return True, f"แทนที่ข้อมูลเดิมเรียบร้อย: ส่งข้อมูลชุดใหม่ {len(records):,} รายการเข้า Supabase สำเร็จ"

    except Exception as e:
        return False, str(e)


upload_processed_data = upload_processed_excel_sheet
