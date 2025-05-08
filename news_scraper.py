import requests
from bs4 import BeautifulSoup
from datetime import datetime

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
    except:
        return "본문 요청 실패"

url = "https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=101"
res = requests.get(url)
soup = BeautifulSoup(res.text, 'html.parser')
articles = soup.select('.rankingnews_box a')

results = {k: [] for k in keywords}
for article in articles:
    title = article.text.strip()
    link = "https://news.naver.com" + article['href']
    for category, words in keywords.items():
        if any(word in title for word in words):
            if len(results[category]) < 10:
                paragraph = extract_first_paragraph(link)
                results[category].append((title, link, paragraph))
            break

today = datetime.now().strftime('%Y-%m-%d')
with open(f"output_{today}.md", "w", encoding="utf-8") as f:
    f.write(f"# 📅 {today} 네이버 경제 키워드 뉴스 요약\n\n")
    for cat, items in results.items():
        if len(items) >= 3:
            f.write(f"## 📌 {cat}\n\n")
            for i, (title, link, para) in enumerate(items[:10], 1):
                f.write(f"{i}. **{title}**\n   - {para}\n   - [기사 링크]({link})\n\n")
