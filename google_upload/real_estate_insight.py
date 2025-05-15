import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import os
import base64
import requests

# credentials 설정
b64_cred = os.environ['GOOGLE_CREDENTIALS']
os.makedirs("google_upload", exist_ok=True)
with open("google_upload/credentials.json", "w") as f:
    f.write(base64.b64decode(b64_cred).decode('utf-8'))

SERVICE_ACCOUNT_FILE = 'google_upload/credentials.json'
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'
SHEET_NAME = '요약결과'

def get_today_summary():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SHEET_NAME)
    
    records = ws.get_all_values()
    today = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d')
    
    for row in records[::-1]:  # 최근 행부터 역순으로 탐색
        if row[0] == today:
            return row[1], ws
    
    return None, ws

def get_real_estate_insight(text_block):
    prompt = f"""너는 한국의 서울 아파트 투자 분석가야. 아래 뉴스 요약을 읽고, 서울아파트 투자 관점에서 의미 있는 시사점이나 트렌드를 5문단 이내로 정리해줘.

{text_block}

형식: 부동산 투자 관점에서 요약된 분석 문단 (5문단 이내)
"""
    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 300,
        "temperature": 0.5,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    return response.json()["content"][0]["text"].strip()

def main():
    today = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d')
    text_block, ws = get_today_summary()
    
    if not text_block:
        print(f"{today}에 해당하는 뉴스 요약이 없습니다.")
        return

    insight = get_real_estate_insight(text_block)
    
    # 시트 크기 조정 (필요한 경우)
    if ws.col_count < 3:
        ws.resize(rows=ws.row_count, cols=3)
    
    # 시트 오른쪽 셀에 인사이트 저장
    cell = ws.find(today)
    if cell:
        ws.update_cell(cell.row, 3, insight)
        print("부동산 인사이트 저장 완료")
    else:
        print("행을 찾을 수 없음")

if __name__ == "__main__":
    main()
