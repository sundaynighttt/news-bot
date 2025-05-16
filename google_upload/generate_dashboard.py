import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from jinja2 import Template

# 이미 인증된 credentials가 있으므로 재활용
SERVICE_ACCOUNT_FILE = 'google_upload/credentials.json'
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'  # 실제 ID로 교체
SOURCE_SHEET = '요약결과'

def get_latest_summary():
    # 구글 시트 설정
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    # 시트 데이터 가져오기
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SOURCE_SHEET)
    
    # 최신 데이터 가져오기
    rows = ws.get_all_values()
    if len(rows) <= 1:  # 헤더만 있는 경우
        return None, None
    
    latest_row = rows[-1]  # 가장 최근 행
    date = latest_row[0]
    summary = latest_row[1]
    insight = latest_row[2] if len(latest_row) > 2 else ""
    
    return date, summary, insight

def extract_categories(summary_text):
    # 앞서 작성한 extract_categories 함수와 동일
    # 카테고리별 데이터 추출 로직
    categories = {}
    current_category = None
    trend = None
    items = []
    
    lines = summary_text.split('\n')
    
    for i, line in enumerate(lines):
        # 날짜 라인 무시
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
            
            # 새 카테고리 설정
            current_category = line.replace("【", "").replace("】", "").strip()
            trend = None
            items = []
            
        # 트렌드 라인 (💡 으로 시작)
        elif line.startswith("💡") and current_category:
            trend = line.replace("💡", "").strip()
            
        # 뉴스 항목 (숫자로 시작하는 라인)
        elif line.strip() and line[0].isdigit() and ". " in line and current_category:
            title = line.split(". ", 1)[1].strip()
            # 요약이 다음 라인에 있는지 확인
            if i+1 < len(lines) and "→" in lines[i+1]:
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

def analyze_insight(insight_text):
    # 앞서 작성한 analyze_insight 함수와 동일
    # 인사이트 분석 로직
    risks = []
    opportunities = []
    scenarios = {
        'positive': '',
        'neutral': '',
        'negative': ''
    }
    
    lines = insight_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 위험요인 섹션 찾기
        if "위험" in line or "리스크" in line:
            current_section = "risks"
            continue
            
        # 기회요인 섹션 찾기
        if "기회" in line or "강점" in line or "긍정" in line:
            current_section = "opportunities"
            continue
            
        # 시나리오 섹션 찾기
        if "긍정적" in line or "낙관적" in line:
            current_section = "positive"
            continue
        if "중립" in line or "기본" in line:
            current_section = "neutral"
            continue
        if "부정적" in line or "비관적" in line:
            current_section = "negative"
            continue
            
        # 현재 섹션에 내용 추가
        if current_section == "risks" and line.startswith("-"):
            risks.append(line.replace("-", "").strip())
        elif current_section == "opportunities" and line.startswith("-"):
            opportunities.append(line.replace("-", "").strip())
        elif current_section in ["positive", "neutral", "negative"]:
            scenarios[current_section] += line + " "
    
    return {
        'risks': risks,
        'opportunities': opportunities,
        'scenarios': scenarios
    }

def generate_html_dashboard():
    # 필요한 데이터 가져오기
    date, summary, insight = get_latest_summary()
    if not date or not summary:
        print("데이터를 찾을 수 없습니다.")
        return
    
    # 데이터 구조화
    categories = extract_categories(summary)
    insights = analyze_insight(insight)
    
    # HTML 템플릿 만들기
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>한국 경제 및 부동산 시장 분석 ({date})</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Noto Sans KR', sans-serif;
        }}
        
        /* CSS 스타일 전체 복사 */
        /* 여기에 CSS 복사 */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>한국 경제 및 부동산 시장 분석</h1>
            <div class="header-date">{date}</div>
        </div>
        
        <div class="section categories">
            <h2><span class="emoji">📊</span> 카테고리별 주요 키워드</h2>
            <table class="category-table">
                <tr>
                    <th>카테고리</th>
                    <th>주요 이슈</th>
                </tr>
    """
    
    # 카테고리별 내용 추가
    for category, data in categories.items():
        html += f"""
                <tr>
                    <td><strong>{category}</strong></td>
                    <td>
        """
        
        for item in data['items']:
            html += f"""
                        - {item['title']}<br>
            """
            
        html += """
                    </td>
                </tr>
        """
    
    # 나머지 섹션 추가
    html += """
            </table>
        </div>
        
        <!-- 여기에 나머지 섹션 추가 -->
        
    </div>
</body>
</html>
    """
    
    # HTML 파일 저장
    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("대시보드 HTML이 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    generate_html_dashboard()
