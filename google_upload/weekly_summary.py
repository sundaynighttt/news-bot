import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from collections import defaultdict
import os
import base64
import requests
from logging_config import setup_logger, log_execution_time
from error_handler import error_handler

# 로거 설정
logger = setup_logger('weekly_summary')
start_time = datetime.now()

# 복호화된 credentials 생성
b64_cred = os.environ['GOOGLE_CREDENTIALS']
os.makedirs("google_upload", exist_ok=True)
with open("google_upload/credentials.json", "w") as f:
    f.write(base64.b64decode(b64_cred).decode('utf-8'))

SERVICE_ACCOUNT_FILE = 'google_upload/credentials.json'
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'
SOURCE_SHEET = '뉴스요약'
TARGET_SHEET = '주간요약'

def fetch_week_news():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SOURCE_SHEET)
    rows = ws.get_all_values()[1:]

    today = datetime.now() + timedelta(hours=9)
    week_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    filtered = [r for r in rows if r[0] in week_dates and "본문 추출 실패" not in r[3]]
    return filtered, sh

def get_weekly_summary(texts):
    prompt = f"""아래는 이번 주의 주요 경제 뉴스 기사들입니다. 이 내용을 요약하여 아파트 투자자 입장에서 의미 있는 인사이트를 제시해주세요.
    
{texts}

요약:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 500,
        "temperature": 0.5,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        return response.json()["content"][0]["text"].strip()
    except:
        return "요약 실패"

@error_handler('weekly_summary')
def main():
    logger.info("주간 요약 생성 시작")
    rows, sh = fetch_week_news()
    if not rows:
        logger.warning("이번 주 데이터 없음")
        print("이번 주 데이터 없음")
        return

    grouped = defaultdict(list)
    for row in rows:
        cat, title, summary, link = row[1], row[2], row[3], row[4]
        grouped[cat].append(f"{title}\n{summary}\n{link}")

    today = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d')
    weekly_output = [f"📅 {today} 주간 경제 뉴스 요약\n"]
    
    logger.info("카테고리별 인사이트 생성")
    for cat, texts in grouped.items():
        joined = "\n\n".join(texts[:5])
        insight = get_weekly_summary(joined)
        weekly_output.append(f"📌 {cat} 인사이트\n{insight}\n")

    output_text = "\n\n".join(weekly_output)

    logger.info("Google Sheets에 저장")
    try:
        ws = sh.worksheet(TARGET_SHEET)
    except:
        ws = sh.add_worksheet(title=TARGET_SHEET, rows="100", cols="2")
        ws.append_row(["날짜", "요약"])
    
    ws.append_row([today, output_text], value_input_option='RAW')
    logger.info("주간 요약 저장 완료")
    log_execution_time(logger, start_time, 'weekly_summary')
    
    print(output_text)

if __name__ == "__main__":
    main()
