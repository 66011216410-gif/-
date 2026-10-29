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

        # สร้าง/เขียนทับคอลัมน์ "ไทย-ต่างชาติ" จาก "สัญชาติ(th)" ทุกครั้ง
        # เพื่อไม่ใช้ค่าคอลัมน์เดิมที่อาจไม่ตรงกับสัญชาติจริง
        if "สัญชาติ(th)" in result_df.columns:
            nationality = result_df["สัญชาติ(th)"].astype("string").str.strip()
            is_blank = (
                nationality.isna()
                | nationality.eq("")
                | nationality.str.casefold().eq("nan")
            )
            is_thai = nationality.str.contains(
                r"ไทย|thai", case=False, regex=True, na=False
            )
            result_df["ไทย-ต่างชาติ"] = pd.Series(
                [
                    pd.NA if blank else ("ไทย" if thai else "ต่างชาติ")
                    for thai, blank in zip(is_thai.tolist(), is_blank.tolist())
                ],
                index=result_df.index,
                dtype="string",
            )

        # ตรวจข้อมูลซ้ำโดยอัตโนมัติ และแสดงสรุปผลบนหน้าแอปทันที
        st.subheader("🔎 ผลการตรวจสอบข้อมูลซ้ำ")

        duplicate_id_rows = pd.DataFrame()
        duplicate_id_count = 0
        if "รหัสนิสิต" in result_df.columns:
            student_ids = result_df["รหัสนิสิต"].astype("string").str.strip()
            valid_ids = (
                student_ids.notna()
                & student_ids.ne("")
                & ~student_ids.str.casefold().eq("nan")
            )
            duplicate_id_mask = valid_ids & student_ids.duplicated(keep=False)
            duplicate_id_rows = result_df.loc[duplicate_id_mask].copy()
            duplicate_id_count = int(
                student_ids[valid_ids].duplicated(keep="first").sum()
            )

            if duplicate_id_count:
                st.warning(
                    f"⚠️ พบข้อมูลรหัสนิสิตซ้ำ {duplicate_id_count} รหัส "
                    f"({len(duplicate_id_rows)} แถวที่มีรหัสซ้ำ)"
                )
                st.dataframe(duplicate_id_rows, use_container_width=True)
            else:
                st.success("✅ ไม่พบรหัสนิสิตซ้ำ")
        else:
            st.error("❌ ไม่มีคอลัมน์ ‘รหัสนิสิต’ จึงตรวจรหัสนิสิตซ้ำไม่ได้")

        duplicate_row_mask = result_df.duplicated(keep=False)
        duplicate_rows = result_df.loc[duplicate_row_mask].copy()
        duplicate_row_count = int(result_df.duplicated(keep="first").sum())

        if duplicate_row_count:
            st.warning(
                f"⚠️ พบแถวข้อมูลที่ซ้ำกันทุกคอลัมน์ {duplicate_row_count} รายการ "
                f"({len(duplicate_rows)} แถวรวมรายการซ้ำ)"
            )
            st.dataframe(duplicate_rows, use_container_width=True)
        else:
            st.success("✅ ไม่พบแถวข้อมูลที่เหมือนกันทุกคอลัมน์")

        if duplicate_id_count == 0 and duplicate_row_count == 0:
            st.info("ผลตรวจสอบ: ไม่พบข้อมูลซ้ำตามเงื่อนไขทั้งสองแบบ")
        else:
            st.info(
                "ผลตรวจสอบ: พบข้อมูลซ้ำ กรุณาตรวจสอบรายการด้านบน "
                "ระบบยังคงเก็บข้อมูลไว้ทั้งหมดและไม่ลบรายการให้อัตโนมัติ"
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
