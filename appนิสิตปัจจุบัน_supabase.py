import io
import hashlib
import runpy

import pandas as pd
import streamlit as st

# รันเว็บหลักเดิมก่อน
runpy.run_path("appนิสิตปัจจุบัน.py", run_name="__main__")

# หลังจากเว็บหลักประมวลผลสำเร็จ ใช้ Sheet "ข้อมูลประมวลผล"
# ของไฟล์ผลลัพธ์เป็นต้นทางส่งเข้า Supabase โดยตรง
processed = st.session_state.get("processed")

if processed is not None and isinstance(processed, pd.DataFrame) and not processed.empty:
    try:
        from supabase_sync import upload_processed_excel_sheet

        # สร้าง Excel ผลลัพธ์ในหน่วยความจำ แล้วอ่าน Sheet "ข้อมูลประมวลผล"
        # กลับมาเป็น DataFrame อีกครั้ง เพื่อให้ส่งตามข้อมูลใน Sheet จริง
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            processed.to_excel(writer, sheet_name="ข้อมูลประมวลผล", index=False)
        excel_buffer.seek(0)

        result_df = pd.read_excel(
            excel_buffer,
            sheet_name="ข้อมูลประมวลผล",
            dtype=object,
        )

        # ตรวจว่า Sheet มีข้อมูลจริงก่อนส่ง
        if result_df.empty:
            st.warning("⚠️ Sheet ข้อมูลประมวลผลไม่มีข้อมูล จึงยังไม่ส่งเข้า Supabase")
        else:
            # ใช้ลายเซ็นของ Sheet ป้องกันการส่งซ้ำ และทำให้ประมวลผลไฟล์ใหม่แล้วส่งใหม่ได้
            signature_source = pd.util.hash_pandas_object(
                result_df.fillna(""), index=True
            ).values.tobytes()
            sheet_signature = hashlib.sha256(signature_source).hexdigest()

            last_signature = st.session_state.get("supabase_sheet_signature")

            if sheet_signature != last_signature:
                ok, message = upload_processed_excel_sheet(result_df)

                if ok:
                    st.session_state["supabase_sheet_signature"] = sheet_signature
                    st.success("☁️ " + message)
                else:
                    # ไม่บันทึก signature เมื่อส่งไม่สำเร็จ เพื่อให้ retry ได้
                    st.error("❌ ไม่สามารถส่งข้อมูลเข้า Supabase: " + message)
            else:
                st.info("☁️ ข้อมูล Sheet นี้ถูกส่งเข้า Supabase แล้ว")

    except Exception as e:
        st.error(f"❌ ไม่สามารถอ่าน/ส่ง Sheet ข้อมูลประมวลผลเข้า Supabase: {e}")
