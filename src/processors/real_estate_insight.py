import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils import (
    get_kst_date,
    get_all_values,
    update_cell,
    find_cell,
    generate_real_estate_insight
)
from src.config import SPREADSHEET_ID, TARGET_SHEET


def get_today_summary():
    """오늘자 요약 데이터 가져오기"""
    records = get_all_values(SPREADSHEET_ID, TARGET_SHEET, skip_headers=False)
    today = get_kst_date()
    
    for row in records[::-1]:  # 최근 행부터 역순으로 탐색
        if row[0] == today:
            return row[1], None
    
    return None, None


def main():
    """메인 실행 함수"""
    today = get_kst_date()
    text_block, _ = get_today_summary()
    
    if not text_block:
        print(f"{today}에 해당하는 뉴스 요약이 없습니다.")
        return

    insight = generate_real_estate_insight(text_block)
    
    # 오늘 날짜의 셀 찾기
    cell = find_cell(SPREADSHEET_ID, TARGET_SHEET, today)
    
    if cell:
        # 부동산 인사이트를 3번째 컬럼에 저장
        update_cell(SPREADSHEET_ID, TARGET_SHEET, cell.row, 3, insight)
        print("부동산 인사이트 저장 완료")
    else:
        print("오늘 날짜의 행을 찾을 수 없습니다.")


if __name__ == "__main__":
    main()
