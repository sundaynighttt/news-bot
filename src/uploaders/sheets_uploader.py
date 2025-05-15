import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils import get_kst_date, get_year_month_path, append_row_to_sheet
from src.config import SPREADSHEET_ID, SOURCE_SHEET, RAW_DATA_DIR, PROCESSED_DATA_DIR


def upload_csv_to_google_sheets(csv_file):
    """CSV 파일을 Google Sheets에 업로드"""
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            append_row_to_sheet(SPREADSHEET_ID, SOURCE_SHEET, row)


def convert_md_to_csv(md_file, csv_file):
    """Markdown 파일을 CSV로 변환"""
    with open(md_file, 'r', encoding='utf-8') as md, open(csv_file, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['날짜', '카테고리', '제목', '요약', '링크'])

        lines = md.readlines()
        current_cat = None
        date = os.path.basename(md_file).split("_")[-1].replace(".md", "")

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


def main():
    """메인 실행 함수"""
    today = get_kst_date()
    year_month = get_year_month_path()
    
    # 입력 파일 경로 (RAW_DATA_DIR에서 읽기)
    md_dir = os.path.join(RAW_DATA_DIR, year_month)
    md_file = os.path.join(md_dir, f"output_{today}.md")
    
    # 출력 파일 경로 (PROCESSED_DATA_DIR에 저장)
    csv_dir = os.path.join(PROCESSED_DATA_DIR, year_month)
    os.makedirs(csv_dir, exist_ok=True)
    csv_file = os.path.join(csv_dir, f"output_{today}.csv")
    
    convert_md_to_csv(md_file, csv_file)
    upload_csv_to_google_sheets(csv_file)
    
    print(f"CSV 변환 및 업로드 완료: {csv_file}")


if __name__ == "__main__":
    main()
