import runpy
import streamlit as st

# รันเว็บหลักเดิมก่อน โดยไม่ต้องแก้โค้ดเดิม
runpy.run_path("appนิสิตปัจจุบัน.py", run_name="__main__")

# หลังจากเว็บหลักประมวลผลสำเร็จ ให้ส่งข้อมูลประมวลผลเข้า Supabase
processed = st.session_state.get("processed")

if processed is not None and not st.session_state.get("supabase_synced", False):
    try:
        from supabase_sync import upload_processed_data

        ok, message = upload_processed_data(processed)
        if ok:
            st.session_state["supabase_synced"] = True
            st.success("☁️ " + message)
        else:
            st.error("ไม่สามารถส่งข้อมูลเข้า Supabase: " + message)
    except Exception as e:
        st.error(f"ไม่สามารถส่งข้อมูลเข้า Supabase: {e}")
