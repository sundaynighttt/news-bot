import csv
import gspread
import base64
import os
from google.oauth2.service_account import Credentials
from datetime import datetime

# 복호화 후 credentials.json 파일 생성
b64_cred = os.environ['GOOGLE_CREDENTIALS']
os.makedirs("google_upload", exist_ok=True)
with open("google_upload/credentials.json", "w") as f:
    f.write(base64.b64decode(b64_cred).decode('utf-8'))

SERVICE_ACCOUNT_FILE = 'google_upload/credentials.json'
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'
SHEET_NAME = '뉴스요약'

def upload_csv_to_google_sheets(csv_file):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
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
            elif line.strip().startswith("1.") or (len(line.strip()) > 1 and line.strip()[0].isdigit() and line.strip()[1] == "."):
                try:
                    title_line = line.strip().split("**")[1]
                    summary = lines[i + 1].replace("- ", "").strip()
                    link = lines[i + 2].split("(")[-1].rstrip(")")
                    writer.writerow([date, current_cat, title_line, summary, link])
                except:
                    continue

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    md_file = f"output_{today}.md"
    csv_file = f"output_{today}.csv"
    convert_md_to_csv(md_file, csv_file)
    upload_csv_to_google_sheets(csv_file)
