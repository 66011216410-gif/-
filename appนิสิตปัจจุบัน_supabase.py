import io
import runpy

import pandas as pd
import streamlit as st

# รันเว็บหลักเดิมก่อน
runpy.run_path("appนิสิตปัจจุบัน.py", run_name="__main__")

# หลังจากเว็บหลักประมวลผลสำเร็จ ให้ใช้ข้อมูลจาก Sheet "ข้อมูลประมวลผล"
# ของไฟล์ผลลัพธ์เป็นต้นทางในการส่งเข้า Supabase โดยตรง
processed = st.session_state.get("processed")

if processed is not None and not st.session_state.get("supabase_synced", False):
    try:
        from supabase_sync import upload_processed_excel_sheet

        # สร้างไฟล์ Excel ผลลัพธ์ในหน่วยความจำ แล้วอ่าน Sheet "ข้อมูลประมวลผล"
        # กลับมาอีกครั้ง เพื่อให้โครงสร้างที่ส่งเข้า Supabase ตรงกับ Sheet ผลลัพธ์
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            processed.to_excel(writer, sheet_name="ข้อมูลประมวลผล", index=False)
        excel_buffer.seek(0)

        result_df = pd.read_excel(
            excel_buffer,
            sheet_name="ข้อมูลประมวลผล",
            dtype=object,
        )

        ok, message = upload_processed_excel_sheet(result_df)
        if ok:
            st.session_state["supabase_synced"] = True
            st.success("☁️ " + message)
        else:
            st.error("ไม่สามารถส่งข้อมูลเข้า Supabase: " + message)
    except Exception as e:
        st.error(f"ไม่สามารถส่งข้อมูลเข้า Supabase: {e}")
