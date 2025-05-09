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

def get_one_line_summary(title, content):
    """뉴스를 한 줄로 간단히 요약"""
    prompt = f"""다음 뉴스를 20자 이내로 핵심만 요약하세요.

제목: {title}
내용: {content[:300]}

규칙:
- 20자 이내
- 대괄호 [] 사용 금지
- 핵심 키워드와 내용만 포함
- 완전한 문장으로 끝맺음

예시:
강남아파트 매도 75% 급증
금리인상으로 대출금리 상승

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
            result = response.json()["content"][0]["text"].strip()
            # 대괄호 제거
            result = result.replace("[", "").replace("]", "")
            # 길이 초과시 자르기
            if len(result) > 30:
                result = result[:27] + "..."
            return result
        else:
            return f"{title[:20]}..."
    except Exception as e:
        print(f"API 오류: {e}")
        return f"{title[:20]}..."

def get_category_trend(items):
    """카테고리별 핵심 트렌드 한 줄 요약"""
    titles = [item[0] for item in items[:3]]
    
    prompt = f"""다음 뉴스들의 핵심 트렌드를 15자 이내로 요약하세요.

{chr(10).join(titles)}

규칙:
- 15자 이내
- 번호나 리스트 금지
- 하나의 완전한 문장
- 대괄호 사용 금지

예시:
금리인상 우려 확산
부동산 거래 활발

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
            result = response.json()["content"][0]["text"].strip()
            # 번호나 리스트 제거
            result = result.split("1.")[0].strip()
            result = result.replace("[", "").replace("]", "")
            if len(result) > 20:
                result = result[:17] + "..."
            return result
        else:
            return "주요 동향"
    except:
        return "주요 동향"

def compose_kakao_message(grouped):
    """카카오톡에 최적화된 메시지 구성"""
    today_str = datetime.now().strftime('%m/%d')
    lines = [f"📅 {today_str} 경제뉴스\n"]
    
    for cat, items in grouped.items():
        lines.append(f"【{cat}】")
        
        # 카테고리 트렌드
        trend = get_category_trend(items)
        lines.append(f"💡 {trend}")
        
        # 각 기사 한 줄 요약 (최대 5개)
        for idx, (title, content, link) in enumerate(items[:5], 1):
            summary = get_one_line_summary(title, content)
            lines.append(f"{idx}. {summary}")
        
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
