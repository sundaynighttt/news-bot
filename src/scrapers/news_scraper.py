import os
import sys
import requests
from bs4 import BeautifulSoup

# 프로젝트 루트를 Python path에 추가 (GitHub Actions 호환성 유지)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils import get_kst_date, get_year_month_path
from src.config import KEYWORDS, NEWS_URL, RAW_DATA_DIR


def extract_first_paragraph(url):
    """뉴스 기사의 첫 번째 문단 추출"""
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
    except:
        return "본문 요청 실패"


def main():
    """메인 실행 함수"""
    res = requests.get(NEWS_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.select('.rankingnews_box a')

    results = {k: [] for k in KEYWORDS}
    for article in articles:
        title = article.text.strip()
        href = article['href']
        if not href.startswith("http"):
            link = "https://news.naver.com" + href
        else:
            link = href

        for category, words in KEYWORDS.items():
            if any(word in title for word in words):
                if len(results[category]) < 10:
                    paragraph = extract_first_paragraph(link)
                    results[category].append((title, link, paragraph))
                break

    # 날짜별 폴더 생성
    today = get_kst_date()
    year_month = get_year_month_path()
    output_dir = os.path.join(RAW_DATA_DIR, year_month)
    os.makedirs(output_dir, exist_ok=True)
    
    # 저장 경로
    output_file = os.path.join(output_dir, f"output_{today}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# 📅 {today} 네이버 경제 키워드 뉴스 요약\n\n")
        for cat, items in results.items():
            if len(items) >= 3:
                f.write(f"## 📌 {cat}\n\n")
                for i, (title, link, para) in enumerate(items[:10], 1):
                    f.write(f"{i}. **{title}**\n   - {para}\n   - [기사 링크]({link})\n\n")
    
    print(f"뉴스 수집 완료: {output_file}")


if __name__ == "__main__":
    main()
