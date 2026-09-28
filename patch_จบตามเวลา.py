import pandas as pd


def add_graduation_on_time_column(work: pd.DataFrame) -> pd.DataFrame:
    """เพิ่มคอลัมน์ 'จบตามเวลา'

    เงื่อนไข:
    - ป.โท: จบภายใน 2 ปี -> 'จบตามเวลา'
    - ป.เอก: จบภายใน 4 ปี -> 'จบตามเวลา'
    - นอกเหนือจากนี้ -> 'เกินเวลา'
    - ถ้ายังไม่มีระยะเวลา หรือยังไม่สำเร็จการศึกษา -> 'ยังไม่จบ'
    """
    result = work.copy()
    level = result["ระดับ"].astype(str).str.strip()
    duration = pd.to_numeric(result["ระยะเวลา(ปี)"], errors="coerce")
    status = result["สถานะนิสิต"].astype(str).str.strip()

    result["จบตามเวลา"] = "ยังไม่จบ"
    graduated = status == "สำเร็จการศึกษา"
    result.loc[graduated & duration.notna(), "จบตามเวลา"] = "เกินเวลา"
    result.loc[graduated & (level == "ป.โท") & (duration <= 2), "จบตามเวลา"] = "จบตามเวลา"
    result.loc[graduated & (level == "ป.เอก") & (duration <= 4), "จบตามเวลา"] = "จบตามเวลา"
    return result
