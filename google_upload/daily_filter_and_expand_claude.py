import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from collections import defaultdict
import os
import base64
import requests

# 복호화된 credentials 생성
b64_cred = os.environ['GOOGLE_CREDENTIALS']
os.makedirs("google_upload", exist_ok=True)
with open("google_upload/credentials.json", "w") as f:
    f.write(base64.b64decode(b64_cred).decode('utf-8'))

# 구글 시트 설정
SERVICE_ACCOUNT_FILE = 'google_upload/credentials.json'
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'
SOURCE_SHEET = '뉴스요약'
TARGET_SHEET = '요약결과'

def fetch_today_news():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SOURCE_SHEET)
    rows = ws.get_all_values()[1:]  # header 제외

    today = datetime.now().strftime('%Y-%m-%d')
    filtered = [r for r in rows if r[0] == today and "본문 추출 실패" not in r[3]]
    return filtered, sh

def get_title_summary(title):
    """제목을 간단히 정리 (특수문자 제거, 핵심만 추출)"""
    prompt = f"""다음 뉴스 제목을 25자 이내로 핵심만 요약하세요.

제목: {title}

규칙:
- 25자 이내
- 불필요한 특수문자나 따옴표 제거
- 핵심 키워드와 주요 내용만 포함

예시:
입력: [단독] "이러다 삼성에 다 뺏긴다" '초유의 사태' 애플, 15년만에 내놓은 역대급 기능?
출력: 애플 나의찾기 15년만 국내 출시

요약:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", 
                               headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            # 제목에서 특수문자 제거하고 앞부분만 반환
            clean_title = title.replace('"', '').replace("'", '').replace('[단독]', '').strip()
            return clean_title[:25]
    except:
        return title[:25]

def get_content_summary(content):
    """본문의 핵심 내용 한 줄 요약"""
    prompt = f"""다음 뉴스 내용의 핵심을 20자 이내로 요약하세요.

내용: {content[:500]}

규칙:
- 20자 이내
- 핵심 사실이나 수치 포함
- 원인이나 영향 중심으로 요약

예시:
입력: 서울 강남구에서 20년 이상 보유한 아파트의 매도가 급증했다. 상급지로의 이동 수요와 절세 목적의 현금화가 주요 원인으로 분석된다.
출력: 상급지 이동과 절세 목적 현금화

요약:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", 
                               headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            return "주요 내용 요약 실패"
    except:
        return "요약 오류"

def get_category_trend(items):
    """카테고리별 핵심 트렌드"""
    titles = [item[0] for item in items[:3]]
    
    prompt = f"""다음 뉴스들의 공통 트렌드를 15자 이내로 요약하세요.

{chr(10).join(titles)}

규칙:
- 15자 이내
- 하나의 간결한 문장
- 공통되는 핵심 주제 파악

요약:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 30,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", 
                               headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            return "주요 동향"
    except:
        return "주요 동향"

def compose_kakao_message(grouped):
    """카카오톡에 최적화된 확장 메시지"""
    today_str = datetime.now().strftime('%m/%d')
    lines = [f"📅 {today_str} 경제뉴스\n"]
    
    for cat, items in grouped.items():
        lines.append(f"【{cat}】")
        
        # 카테고리 트렌드
        trend = get_category_trend(items)
        lines.append(f"💡 {trend}\n")
        
        # 각 기사 제목과 내용 요약
        for idx, (title, content, link) in enumerate(items[:5], 1):
            title_summary = get_title_summary(title)
            content_summary = get_content_summary(content)
            
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
    today = datetime.now().strftime('%Y-%m-%d')
    rows, sh = fetch_today_news()

    grouped = defaultdict(list)
    for row in rows:
        category, title, content, link = row[1], row[2], row[3], row[4]
        grouped[category].append((title, content, link))

    # 카테고리별 5개로 제한
    for cat in grouped:
        grouped[cat] = grouped[cat][:5]

    kakao_message = compose_kakao_message(grouped)
    
    try:
        target_ws = sh.worksheet(TARGET_SHEET)
    except:
        target_ws = sh.add_worksheet(title=TARGET_SHEET, rows="100", cols="2")
        target_ws.append_row(["날짜", "요약"])

    target_ws.append_row([today, kakao_message], value_input_option='RAW')
    
    # 콘솔에도 출력
    print(kakao_message)

if __name__ == "__main__":
    main()
