import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils import (
    get_kst_date, 
    get_kst_date_with_weekday,
    get_sheets_client,
    get_all_values,
    create_worksheet_if_not_exists,
    append_row_to_sheet,
    summarize_title,
    summarize_content,
    get_category_trend
)
from src.config import SPREADSHEET_ID, SOURCE_SHEET, TARGET_SHEET


def fetch_today_news():
    """오늘자 뉴스 데이터를 Google Sheets에서 가져오기"""
    sh = get_sheets_client(SPREADSHEET_ID)
    rows = get_all_values(SPREADSHEET_ID, SOURCE_SHEET)
    
    today = get_kst_date()
    filtered = [r for r in rows if r[0] == today and "본문 추출 실패" not in r[3]]
    return filtered, sh


def compose_kakao_message(grouped):
    """카카오톡에 최적화된 메시지 작성"""
    today_str = get_kst_date_with_weekday()
    
    lines = [f"📅 {today_str} 경제뉴스입니다\n"]
    
    for cat, items in grouped.items():
        lines.append(f"【{cat}】")
        
        # 카테고리 트렌드
        trend = get_category_trend(items)
        lines.append(f"💡 {trend}\n")
        
        # 각 기사 제목과 내용 요약
        for idx, (title, content, link) in enumerate(items[:5], 1):
            title_summary = summarize_title(title)
            content_summary = summarize_content(content)
            
            lines.append(f"{idx}. {title_summary}")
            lines.append(f"   → {content_summary}")
            
            # 기사 사이 간격
            if idx < len(items[:5]):
                lines.append("")
        
        lines.append("")  # 카테고리 사이 공백
    
    # 맨 마지막에 링크 추가
    lines.append("📌 전체뉴스")
    lines.append("https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=101")
    
    return "\n".join(lines)


def main():
    """메인 실행 함수"""
    today = get_kst_date()
    rows, sh = fetch_today_news()

    grouped = defaultdict(list)
    for row in rows:
        category, title, content, link = row[1], row[2], row[3], row[4]
        grouped[category].append((title, content, link))

    # 카테고리별 5개로 제한
    for cat in grouped:
        grouped[cat] = grouped[cat][:5]

    kakao_message = compose_kakao_message(grouped)
    
    # 타겟 워크시트 생성 또는 가져오기
    target_ws = create_worksheet_if_not_exists(
        SPREADSHEET_ID, 
        TARGET_SHEET, 
        rows=100, 
        cols=3,
        headers=["날짜", "요약", "부동산인사이트"]
    )
    
    # 데이터 추가
    append_row_to_sheet(
        SPREADSHEET_ID,
        TARGET_SHEET,
        [today, kakao_message, ""]
    )
    
    # 콘솔에도 출력
    print(kakao_message)


if __name__ == "__main__":
    main()
