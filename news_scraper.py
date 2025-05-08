# news_scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 키워드 설정
keywords = {
    '부동산': ['서울', '아파트', '부동산', '전세', '재건축', '강남'],
    '금리': ['금리', '연준', '인상', '인하', '기준금리', '물가'],
    '해외주식': ['나스닥', '테슬라', '비트코인', 'ETF', '뉴욕증시', 'S&P']
}

# 요청
url = "https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=101"
res = requests.get(url)
soup = BeautifulSoup(res.text, 'html.parser')
articles = soup.select('.rankingnews_box a')

result = {k: [] for k in keywords}
for article in articles:
    title = article.text.strip()
    link = "https://news.naver.com" + article['href']
    for category, keys in keywords.items():
        if any(k in title for k in keys):
            result[category].append((title, link))
            break

# 결과 출력
today = datetime.now().strftime("%Y-%m-%d")
with open(f"output_{today}.md", "w", encoding="utf-8") as f:
    f.write(f"# 📅 {today} 네이버 경제 키워드 뉴스 요약\n\n")
    for cat, items in result.items():
        f.write(f"## 📌 {cat}\n")
        for i, (title, link) in enumerate(items[:3], 1):
            f.write(f"{i}. **{title}**\n   - [기사 링크]({link})\n\n")
