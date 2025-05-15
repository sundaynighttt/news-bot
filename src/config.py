# Configuration for News Bot

# Google Sheets Configuration
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'
SOURCE_SHEET = '뉴스요약'
TARGET_SHEET = '요약결과'
WEEKLY_SHEET = '주간요약'

# API Configuration
ANTHROPIC_MODELS = {
    'haiku': 'claude-3-haiku-20240307',
    'sonnet': 'claude-3-sonnet-20240229'
}

# Scraper Configuration
NEWS_URL = "https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=101"
KEYWORDS = {
    '부동산': ['서울', '아파트', '부동산', '전세', '재건축', '입주', '실거래', '청약', '분양', '매매', '거래량', '중개업소'],
    '금리': ['금리', '연준', '인상', '인하', '기준금리', '물가', 'CPI', '물가상승률', '금통위', '채권', '유동성'],
    '해외주식': ['나스닥', 'S&P', '테슬라', '애플', '엔비디아', '비트코인', 'ETF', '뉴욕증시', 'AI주', '반도체', '미국주식']
}

# Data Configuration
DATA_DIR = 'data'
RAW_DATA_DIR = 'data/raw'
PROCESSED_DATA_DIR = 'data/processed'
LOG_DIR = 'logs'
