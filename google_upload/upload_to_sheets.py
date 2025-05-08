import csv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 서비스 계정 키 경로 및 구글 시트 ID 설정
SERVICE_ACCOUNT_FILE = 'credentials.json'  # 🔐 이 파일은 수동으로 넣어야 함
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'  # 📄 너가 만든 구글 시트 ID로 바꿔야 함
SHEET_NAME = '뉴스요약'  # 원하는 시트 탭 이름

def upload_csv_to_google_sheets(csv_file):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 헤더 건너뜀
        for row in reader:
            worksheet.append_row(row, value_input_option='RAW')

def convert_md_to_csv(md_file, csv_file):
    with open(md_file, 'r', encoding='utf-8') as md, open(csv_file, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['날짜', '카테고리', '제목', '요약', '링크'])

        lines = md.readlines()
        current_cat = None
        date = md_file.split("_")[-1].replace(".md", "")

        for i, line in enumerate(lines):
            if line.startswith("## 📌"):
                current_cat = line.strip().replace("## 📌", "").strip()
            elif line.strip().startswith("1.") or line.strip()[0].isdigit() and line.strip()[1] == ".":
                title_line = line.strip().split("**")[1]
                summary = lines[i + 1].replace("- ", "").strip()
                link = lines[i + 2].split("(")[-1].rstrip(")
")
                writer.writerow([date, current_cat, title_line, summary, link])

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    md_file = f"output_{today}.md"
    csv_file = f"output_{today}.csv"
    convert_md_to_csv(md_file, csv_file)
    upload_csv_to_google_sheets(csv_file)
