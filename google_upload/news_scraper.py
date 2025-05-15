import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
from logging_config import setup_logger, log_execution_time
from error_handler import error_handler

# 로거 설정
logger = setup_logger('news_scraper')
start_time = datetime.now()

keywords = {
    '부동산': ['서울', '아파트', '부동산', '전세', '재건축', '입주', '실거래', '청약', '분양', '매매', '거래량', '중개업소'],
    '금리': ['금리', '연준', '인상', '인하', '기준금리', '물가', 'CPI', '물가상승률', '금통위', '채권', '유동성'],
    '해외주식': ['나스닥', 'S&P', '테슬라', '애플', '엔비디아', '비트코인', 'ETF', '뉴욕증시', 'AI주', '반도체', '미국주식']
}

def extract_first_paragraph(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        content = soup.select_one("#dic_area")
        if content:
            paragraphs = content.get_text(strip=True).split('\n')
            for p in paragraphs:
                if len(p.strip()) > 30:
                    return p.strip()
        return "본문 추출 실패"
    except Exception as e:
        logger.warning(f"URL {url} 처리 중 오류: {str(e)}")
        return "본문 요청 실패"

logger.info("뉴스 수집 시작")

@error_handler('news_scraper', notify_success=True)  # 성공 알림 받기
def main():
    url = "https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=101"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.select('.rankingnews_box a')
    
    logger.info(f"총 {len(articles)}개 기사 발견")
    
    results = {k: [] for k in keywords}
    for article in articles:
        title = article.text.strip()
        href = article['href']
        if not href.startswith("http"):
            link = "https://news.naver.com" + href
        else:
            link = href
    
        for category, words in keywords.items():
            if any(word in title for word in words):
                if len(results[category]) < 10:
                    paragraph = extract_first_paragraph(link)
                    results[category].append((title, link, paragraph))
                break
    
    # 날짜별 폴더 생성
    today = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d')
    year_month = (datetime.now() + timedelta(hours=9)).strftime('%Y/%m')
    output_dir = f"data/raw/{year_month}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 파일 저장
    output_file = f"{output_dir}/output_{today}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# 📅 {today} 네이버 경제 키워드 뉴스 요약\n\n")
        for cat, items in results.items():
            if len(items) >= 3:
                logger.info(f"{cat} 카테고리: {len(items)}개 기사 수집")
                f.write(f"## 📌 {cat}\n\n")
                for i, (title, link, para) in enumerate(items[:10], 1):
                    f.write(f"{i}. **{title}**\n   - {para}\n   - [기사 링크]({link})\n\n")
    
    logger.info(f"데이터 저장 완료: {output_file}")
    log_execution_time(logger, start_time, 'news_scraper')

if __name__ == "__main__":
    main()
