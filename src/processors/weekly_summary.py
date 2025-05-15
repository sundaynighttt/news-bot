import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils import (
    get_kst_date,
    get_week_dates,
    get_all_values,
    create_worksheet_if_not_exists,
    append_row_to_sheet,
    generate_weekly_summary
)
from src.config import SPREADSHEET_ID, SOURCE_SHEET, WEEKLY_SHEET


def fetch_week_news():
    """일주일간의 뉴스 데이터 가져오기"""
    rows = get_all_values(SPREADSHEET_ID, SOURCE_SHEET)
    week_dates = get_week_dates()
    filtered = [r for r in rows if r[0] in week_dates and "본문 추출 실패" not in r[3]]
    return filtered


def main():
    """메인 실행 함수"""
    rows = fetch_week_news()
    
    if not rows:
        print("이번 주 데이터가 없습니다.")
        return

    grouped = defaultdict(list)
    for row in rows:
        cat, title, summary, link = row[1], row[2], row[3], row[4]
        grouped[cat].append(f"{title}\n{summary}\n{link}")

    today = get_kst_date()
    weekly_output = [f"📅 {today} 주간 경제 뉴스 요약\n"]
    
    for cat, texts in grouped.items():
        joined = "\n\n".join(texts[:5])
        insight = generate_weekly_summary(joined)
        weekly_output.append(f"📌 {cat} 인사이트\n{insight}\n")

    output_text = "\n\n".join(weekly_output)

    # 주간요약 워크시트 생성 또는 가져오기
    ws = create_worksheet_if_not_exists(
        SPREADSHEET_ID,
        WEEKLY_SHEET,
        rows=100,
        cols=2,
        headers=["날짜", "요약"]
    )
    
    # 데이터 추가
    append_row_to_sheet(
        SPREADSHEET_ID,
        WEEKLY_SHEET,
        [today, output_text]
    )
    
    print(output_text)


if __name__ == "__main__":
    main()
