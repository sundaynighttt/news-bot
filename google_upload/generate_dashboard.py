# google_upload/generate_dashboard.py 파일
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 시트 설정
SERVICE_ACCOUNT_FILE = 'google_upload/credentials.json'
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'  # 실제 ID로 교체
SOURCE_SHEET = '요약결과'

def main():
    # 구글 시트 연결
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    # 시트 데이터 가져오기
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SOURCE_SHEET)
    
    # 헤더 제외한 모든 데이터
    all_rows = ws.get_all_values()[1:]
    
    # docs 폴더 생성
    os.makedirs("docs", exist_ok=True)
    
    # 인덱스 페이지 생성
    create_index_page(all_rows)
    
    # 각 날짜별 페이지 생성
    for row in all_rows:
        if len(row) >= 3:  # 날짜, 요약, 인사이트가 있는 경우
            date, summary, insight = row[0], row[1], row[2]
            create_date_page(date, summary, insight)
    
    print("대시보드 생성 완료!")

def create_index_page(rows):
    """메인 인덱스 페이지 생성"""
    html = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>경제 및 부동산 분석 대시보드</title>
    <style>
        body { font-family: 'Noto Sans KR', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1, h2 { color: #3a7bd5; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        a { color: #3a7bd5; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>경제 및 부동산 시장 분석 대시보드</h1>
    
    <h2>일별 분석 기록</h2>
    <table>
        <tr>
            <th>날짜</th>
            <th>링크</th>
        </tr>
"""
    
    # 날짜 역순으로 정렬
    sorted_rows = sorted(rows, key=lambda x: x[0], reverse=True)
    
    # 각 날짜별 링크 추가
    for row in sorted_rows:
        date = row[0]
        safe_date = date.replace("/", "-").replace(".", "-")
        html += f"""
        <tr>
            <td>{date}</td>
            <td><a href="{safe_date}.html">분석 보기</a></td>
        </tr>
"""
    
    html += """
    </table>
</body>
</html>"""
    
    # 인덱스 파일 저장
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def create_date_page(date, summary, insight):
    """날짜별 분석 페이지 생성"""
    # 파일명용 날짜 형식 변환
    safe_date = date.replace("/", "-").replace(".", "-")
    
    # 카카오톡 스타일 요약에서 카테고리 정보 추출
    categories = extract_categories(summary)
    
    # 기본 HTML 템플릿
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>경제 분석 - {date}</title>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2 {{ color: #3a7bd5; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; }}
        .back-link {{ margin-bottom: 20px; }}
        .category {{ margin-bottom: 30px; background: #f8f9fa; padding: 15px; border-radius: 8px; }}
        .category h2 {{ margin-top: 0; }}
        .news-item {{ margin-bottom: 10px; }}
        .news-title {{ font-weight: bold; }}
        .news-summary {{ color: #666; margin-left: 20px; }}
        .insight {{ background: #e7f5ff; padding: 15px; border-radius: 8px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="back-link">
        <a href="index.html">← 목록으로 돌아가기</a>
    </div>
    
    <div class="header">
        <h1>경제 및 부동산 분석</h1>
        <div class="date">{date}</div>
    </div>
"""
    
    # 카테고리별 뉴스 추가
    for category, data in categories.items():
        html += f"""
    <div class="category">
        <h2>{category}</h2>
        <div class="trend">💡 {data['trend']}</div>
        <div class="news-list">
"""
        
        for item in data['items']:
            html += f"""
            <div class="news-item">
                <div class="news-title">{item['title']}</div>
                <div class="news-summary">→ {item['summary']}</div>
            </div>
"""
        
        html += """
        </div>
    </div>
"""
    
    # 인사이트 추가
    if insight:
        html += f"""
    <div class="insight">
        <h2>부동산 인사이트</h2>
        <div class="insight-content">
            {insight.replace("\n", "<br>")}
        </div>
    </div>
"""
    
    html += """
</body>
</html>"""
    
    # 파일 저장
    with open(f"docs/{safe_date}.html", "w", encoding="utf-8") as f:
        f.write(html)

def extract_categories(summary_text):
    """카카오톡 스타일 요약에서 카테고리 정보 추출"""
    categories = {}
    current_category = None
    trend = None
    items = []
    
    lines = summary_text.split('\n')
    
    for i, line in enumerate(lines):
        # 날짜 헤더 스킵
        if i == 0 and "경제뉴스입니다" in line:
            continue
            
        # 카테고리 찾기 (【부동산】 형식)
        if "【" in line and "】" in line:
            # 이전 카테고리 저장
            if current_category and trend:
                categories[current_category] = {
                    'trend': trend,
                    'items': items
                }
            
            # 새 카테고리
            current_category = line.replace("【", "").replace("】", "").strip()
            trend = None
            items = []
            
        # 트렌드 찾기 (💡 으로 시작)
        elif line.startswith("💡") and current_category:
            trend = line.replace("💡", "").strip()
            
        # 뉴스 항목 찾기 (숫자로 시작)
        elif line.strip() and line[0].isdigit() and ". " in line and current_category:
            title = line.split(". ", 1)[1].strip()
            
            # 요약이 다음 줄에 있는지 확인
            if i + 1 < len(lines) and "→" in lines[i+1]:
                summary = lines[i+1].strip().replace("→", "").strip()
                items.append({
                    'title': title, 
                    'summary': summary
                })
    
    # 마지막 카테고리 저장
    if current_category and trend:
        categories[current_category] = {
            'trend': trend,
            'items': items
        }
        
    return categories

if __name__ == "__main__":
    main()
