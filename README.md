news-bot/
├── .github/
│   └── workflows/
│       ├── news.yml                 # ✅ 매일 7시: 뉴스 크롤링 → 구글시트 저장
│       └── expand.yml              # ✅ 매일 8시: Claude 요약 → 요약결과 시트에 저장
│
├── google_upload/
│   ├── news_scraper.py             # 📌 네이버 뉴스 수집 (BeautifulSoup)
│   ├── upload_to_sheets.py         # 📌 뉴스 csv → 구글시트 '뉴스요약' 탭에 저장
│   └── daily_filter_and_expand_claude.py  # ✅ Claude로 요약 정리 → '요약결과' 탭 저장
│
├── requirements.txt                # ✅ pip 설치 리스트 (gspread, requests 등)
├── output_YYYY-MM-DD.md            # 📄 수집된 뉴스 원본 마크다운 (자동 생성)
├── output_YYYY-MM-DD.csv           # 📄 변환된 csv 파일 (자동 생성)
└── README.md (선택)                # 📝 프로젝트 설명
