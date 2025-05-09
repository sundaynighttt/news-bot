
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

def run_claude_summary(title, content):
    prompt = f"""Human: 다음 뉴스 제목과 내용을 한 문장으로 요약해줘.
제목: {title}
내용: {content}

Assistant:"""  # triple quotes with escaped newlines

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 200,
        "temperature": 0.5,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    return response.json()["content"][0]["text"].strip()

def compose_markdown(grouped):
    today_str_kor = datetime.now().strftime('%Y년 %m월 %d일')
    lines = [f"{today_str_kor} 경제정보 요약\n"]
    for idx, (cat, items) in enumerate(grouped.items(), 1):
        lines.append(f"{idx}. {cat}")
        for title, summary, link in items:
            lines.append(f"- {title}, {summary}\n  (원문링크: {link})")
        lines.append("")
    return "\n".join(lines)

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    rows, sh = fetch_today_news()

    grouped = defaultdict(list)
    for row in rows:
        category, title, content, link = row[1], row[2], row[3], row[4]
        gpt_summary = run_claude_summary(title, content)
        grouped[category].append((title, gpt_summary, link))

    markdown_summary = compose_markdown(grouped)
    try:
        target_ws = sh.worksheet(TARGET_SHEET)
    except:
        target_ws = sh.add_worksheet(title=TARGET_SHEET, rows="100", cols="2")
        target_ws.append_row(["날짜", "요약"])

    target_ws.append_row([today, markdown_summary], value_input_option='RAW')

if __name__ == "__main__":
    main()
