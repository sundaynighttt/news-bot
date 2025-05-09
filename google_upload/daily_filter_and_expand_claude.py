
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
    prompt = f"""Human: 다음 뉴스 제목과 내용을 한 문장으로 짧게 25자이내로 요약해줘.
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

def emoji_for_category(cat):
    return {
        "부동산": "📌",
        "금리": "💰",
        "해외주식": "📈"
    }.get(cat, "📎")

def compose_markdown(grouped):
    today_str_kor = datetime.now().strftime('%Y년 %m월 %d일')
    lines = [f"✅ {today_str_kor} 경제정보 요약\n"]
    for cat, items in grouped.items():
        emoji = emoji_for_category(cat)
        lines.append(f"\n{emoji} {cat}")
        # 전체 요약 추가
        summaries = [s for _, s, _ in items]
        top_summary = run_claude_summary(cat, "\n".join(summaries[:5]))
        lines.append(f"🧠 요약: {top_summary}\n")
        for title, summary, link in items[:5]:
            short_title = title.strip().split()[0][:12] + ("…" if len(title.strip()) > 12 else "")
            lines.append(f"• 🔹 {short_title}")
            lines.append(f"    📄 AI 요약: {summary}")
            lines.append(f"    🔗 링크: {link}\n")
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
