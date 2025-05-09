
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
    prompt = f"""Human: 아래 뉴스 제목과 본문 내용을 정확히 다음 형식에 맞춰 요약해줘.
형식 예시:

제목요약: 금리 동결
내용요약: 연준 금리 동결 발표 영향

이제 요약할 뉴스는 다음과 같아:

제목: {title}
내용: {content}

Assistant:"""

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

def run_category_summary(titles_and_contents):
    article_list = "\n\n".join([f"제목: {t}\n내용: {c}" for t, c in titles_and_contents])
    prompt = f"""Human: 아래는 같은 분야 뉴스 5개의 제목과 본문 내용이야. 이 5개의 뉴스를 종합해서 하나의 인사이트를 뽑아줘.
형식:
🧠 요약: (하나의 문장으로 종합 요약)

{article_list}

Assistant:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 300,
        "temperature": 0.4,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    return response.json()["content"][0]["text"].strip()

def compose_markdown(grouped):
    today_str_kor = datetime.now().strftime('%Y년 %m월 %d일')
    lines = [f"✅ {today_str_kor} 경제정보 요약\n"]

    for idx, (cat, items) in enumerate(grouped.items(), 1):
        # 카테고리 요약
        category_summary = run_category_summary([(t, c) for t, c, _ in items])
        lines.append(f"\n📌 {cat}\n{category_summary}\n")

        # 기사별 요약
        for title, content, link in items:
            summary = run_claude_summary(title, content)
            lines.append(f"• 🔹 {title}\n📄 AI 요약: {summary}\n🔗 링크: {link}\n")

    return "\n".join(lines)

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    rows, sh = fetch_today_news()

    grouped = defaultdict(list)
    for row in rows:
        category, title, content, link = row[1], row[2], row[3], row[4]
        grouped[category].append((title, content, link))

    # 5개 제한
    for cat in grouped:
        grouped[cat] = grouped[cat][:5]

    markdown_summary = compose_markdown(grouped)
    try:
        target_ws = sh.worksheet(TARGET_SHEET)
    except:
        target_ws = sh.add_worksheet(title=TARGET_SHEET, rows="100", cols="2")
        target_ws.append_row(["날짜", "요약"])

    target_ws.append_row([today, markdown_summary], value_input_option='RAW')

if __name__ == "__main__":
    main()
