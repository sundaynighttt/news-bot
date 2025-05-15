import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from collections import defaultdict
import os
import base64
import requests
from logging_config import setup_logger, log_execution_time
from error_handler import error_handler

# 로거 설정
logger = setup_logger('daily_summary_and_insight')
start_time = datetime.now()

# 투자 관련 핵심 키워드와 가중치
INVESTMENT_KEYWORDS = {
    # 직접적 투자 키워드 (높은 가중치)
    '수익률': 10,
    '투자': 9,
    '매매': 8,
    '시세': 8,
    '가격': 7,
    '상승': 6,
    '하락': 6,
    '수익': 7,
    '손실': 6,
    
    # 간접적 투자 키워드 (중간 가중치)
    '전망': 5,
    '분석': 5,
    '예상': 4,
    '변동': 4,
    '공급': 4,
    '수요': 4,
    
    # 자산 유형 키워드 (기본 가중치)
    '부동산': 3,
    '주식': 3,
    '채권': 3,
    '금': 3,
    '달러': 3,
    '환율': 3
}

# 블랙리스트 키워드 - 이 키워드가 포함된 뉴스는 제외
BLACKLIST_KEYWORDS = [
    '성매매', '성병', '성범죄', '마약', '살인', '폭행',
    '절도', '사기', '도박', '성폭행', '성추행', '아동',
    '음란', '불법', '구속', '체포', '혐의', '기소'
]

# 최소 투자 관련성 점수
MINIMUM_INVESTMENT_SCORE = 10

# 카테고리별 특화 키워드
CATEGORY_KEYWORDS = {
    '부동산': {
        '강남': 5, '재건축': 5, '분양가': 4, 
        '입주물량': 4, '거래량': 4, '규제완화': 5,
        '청약': 4, '대출': 3, '금리': 4
    },
    '금리': {
        '기준금리': 5, '인하': 4, '인상': 4,
        '연준': 5, '한은': 5, '통화정책': 4,
        '물가': 4, 'CPI': 4, '경기': 4
    },
    '해외주식': {
        '나스닥': 4, 'S&P': 4, '실적': 5,
        '배당': 5, 'ETF': 4, '환율': 4,
        '테슬라': 3, '애플': 3, '엔비디아': 3
    }
}

# 복호화된 credentials 생성
b64_cred = os.environ['GOOGLE_CREDENTIALS']
os.makedirs("google_upload", exist_ok=True)
with open("google_upload/credentials.json", "w") as f:
    f.write(base64.b64decode(b64_cred).decode('utf-8'))

# 구글 시트 설정
SERVICE_ACCOUNT_FILE = 'google_upload/credentials.json'
SPREADSHEET_ID = '1KBDB7D5sTvCGM-thDkYCnO-2kvsSoQc4RxDGoOO4Rdk'
SOURCE_SHEET = '뉴스요약'
TARGET_SHEET = '요약결과'

def calculate_investment_score(title, content):
    """투자 관련성 점수 계산"""
    score = 0
    
    # 제목 가중치 (2배)
    for keyword, weight in INVESTMENT_KEYWORDS.items():
        if keyword in title:
            score += weight * 2
    
    # 본문 가중치 (1배)
    if content:
        for keyword, weight in INVESTMENT_KEYWORDS.items():
            if keyword in content[:200]:  # 첫 200자만 확인
                score += weight
    
    return score

def has_blacklist_keywords(title, content):
    """블랙리스트 키워드 포함 여부 확인"""
    text = title + (content[:500] if content else '')
    
    for keyword in BLACKLIST_KEYWORDS:
        if keyword in text:
            return True
    
    return False

def calculate_category_score(title, content, category):
    """카테고리별 특화 키워드 점수"""
    score = 0
    
    if category in CATEGORY_KEYWORDS:
        for keyword, weight in CATEGORY_KEYWORDS[category].items():
            if keyword in title:
                score += weight * 2
            if keyword in content[:200]:
                score += weight
    
    return score

def select_top_investment_news(articles, category, top_n=5):
    """투자 관련성 기준으로 상위 뉴스 선별"""
    scored_articles = []
    filtered_articles = []
    
    # 1단계: 블랙리스트 필터링
    for article in articles:
        title, content, link = article
        if not has_blacklist_keywords(title, content):
            filtered_articles.append(article)
        else:
            logger.debug(f"블랙리스트 필터링: {title}")
    
    # 2단계: 투자 관련성 점수 계산
    for idx, (title, content, link) in enumerate(filtered_articles):
        # 기본 점수: 순서 (최신일수록 높음)
        order_score = len(filtered_articles) - idx
        
        # 투자 관련성 점수
        investment_score = calculate_investment_score(title, content)
        
        # 투자 관련성이 최소 기준 미달인 경우 제외
        if investment_score < MINIMUM_INVESTMENT_SCORE:
            logger.debug(f"투자 관련성 부족: {title} (점수: {investment_score})")
            continue
        
        # 카테고리별 특화 점수
        category_score = calculate_category_score(title, content, category)
        
        # 종합 점수 (가중치 적용)
        total_score = (
            investment_score * 0.5 +  # 50%: 투자 관련성
            category_score * 0.3 +    # 30%: 카테고리 특화
            order_score * 0.2         # 20%: 최신성
        )
        
        scored_articles.append((title, content, link, total_score, investment_score))
        
        # 로깅 추가
        logger.debug(f"{category} - {title}: 투자점수={investment_score}, 카테고리점수={category_score}, 총점={total_score:.2f}")
    
    # 점수 기준 정렬
    sorted_articles = sorted(scored_articles, key=lambda x: x[3], reverse=True)
    
    # 최소 1개, 최대 top_n개 선택 (투자 관련성이 있는 것만)
    selected = [(title, content, link) for title, content, link, _, _ in sorted_articles[:top_n]]
    
    logger.info(f"{category}: {len(articles)}개 중 {len(selected)}개 선택")
    
    return selected

def fetch_today_news():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SOURCE_SHEET)
    rows = ws.get_all_values()[1:]  # header 제외

    # KST 기준 오늘 날짜
    today = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d')
    filtered = [r for r in rows if r[0] == today and "본문 추출 실패" not in r[3]]
    return filtered, sh

def get_title_summary(title):
    """제목을 간단히 정리 (특수문자 제거, 핵심만 추출)"""
    prompt = f"""다음 뉴스 제목을 25자 이내로 핵심만 요약하세요.

제목: {title}

규칙:
- 25자 이내
- 불필요한 특수문자나 따옴표 제거
- 핵심 키워드와 주요 내용만 포함

예시:
입력: [단독] "이러다 삼성에 다 뺏긴다" '초유의 사태' 애플, 15년만에 내놓은 역대급 기능?
출력: 애플 나의찾기 15년만 국내 출시

요약:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", 
                               headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            # 제목에서 특수문자 제거하고 앞부분만 반환
            clean_title = title.replace('"', '').replace("'", '').replace('[단독]', '').strip()
            return clean_title[:25]
    except:
        return title[:25]

def get_content_summary(content):
    """본문의 핵심 내용 한 줄 요약"""
    prompt = f"""다음 뉴스 내용의 핵심을 20자 이내로 요약하세요.

내용: {content[:500]}

규칙:
- 20자 이내
- 핵심 사실이나 수치 포함
- 원인이나 영향 중심으로 요약

예시:
입력: 서울 강남구에서 20년 이상 보유한 아파트의 매도가 급증했다. 상급지로의 이동 수요와 절세 목적의 현금화가 주요 원인으로 분석된다.
출력: 상급지 이동과 절세 목적 현금화

요약:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", 
                               headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            return "주요 내용 요약 실패"
    except:
        return "요약 오류"

def get_category_trend(items):
    """카테고리별 핵심 트렌드"""
    titles = [item[0] for item in items[:3]]
    
    prompt = f"""다음 뉴스들의 공통 트렌드를 15자 이내로 요약하세요.

{chr(10).join(titles)}

규칙:
- 15자 이내
- 하나의 간결한 문장
- 공통되는 핵심 주제 파악

요약:"""

    headers = {
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 30,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", 
                               headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            return "주요 동향"
    except:
        return "주요 동향"

def get_real_estate_insight(text_block):
    """부동산 인사이트 생성"""
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

    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            logger.error(f"부동산 인사이트 API 오류: {response.status_code}")
            return "부동산 인사이트 생성 실패"
    except Exception as e:
        logger.error(f"부동산 인사이트 생성 중 오류: {str(e)}")
        return "부동산 인사이트 생성 오류"

def compose_kakao_message(selected_grouped):
    """카카오톡에 최적화된 확장 메시지"""
    # KST 기준 현재 날짜와 요일 가져오기
    kst_now = datetime.now() + timedelta(hours=9)
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[kst_now.weekday()]
    today_str = kst_now.strftime(f'%m/%d({weekday})')
    
    # 선별된 뉴스가 전혀 없는 경우
    if not any(items for items in selected_grouped.values()):
        return f"📅 {today_str} 경제뉴스입니다\n\n오늘은 투자 관련 뉴스가 없습니다.\n\n📌 전체뉴스\nhttps://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=101"
    
    # 제목에 요일과 "입니다" 추가
    lines = [f"📅 {today_str} 경제뉴스입니다\n"]
    
    for cat, items in selected_grouped.items():
        if items:  # 선별된 기사가 있는 경우만
            lines.append(f"【{cat}】")
            
            # 카테고리 트렌드
            trend = get_category_trend(items)
            lines.append(f"💡 {trend}")
            lines.append(f"(투자 관련 뉴스 {len(items)}개)\n")
            
            # 각 기사 제목과 내용 요약
            for idx, (title, content, link) in enumerate(items, 1):
                title_summary = get_title_summary(title)
                content_summary = get_content_summary(content)
                
                lines.append(f"{idx}. {title_summary}")
                lines.append(f"   → {content_summary}")
                
                # 기사 사이 간격
                if idx < len(items):
                    lines.append("")
            
            lines.append("")  # 카테고리 사이 공백
    
    # 맨 마지막에 링크 추가
    lines.append("📌 전체뉴스")
    lines.append("https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=101")
    
    return "\n".join(lines)

@error_handler('daily_summary_and_insight')
def main():
    # KST 기준 오늘 날짜
    today = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d')
    logger.info("오늘자 뉴스 데이터 가져오기")
    rows, sh = fetch_today_news()

    grouped = defaultdict(list)
    for row in rows:
        category, title, content, link = row[1], row[2], row[3], row[4]
        grouped[category].append((title, content, link))

    # 투자 관련성 기준으로 상위 5개 선별
    selected_grouped = {}
    for cat, articles in grouped.items():
        logger.info(f"{cat} 카테고리: {len(articles)}개 뉴스 중 상위 5개 선별")
        selected_articles = select_top_investment_news(articles, cat)
        selected_grouped[cat] = selected_articles
        logger.info(f"{cat} 카테고리: {len(selected_articles)}개 선별 완료")

    logger.info("카카오톡 메시지 생성")
    kakao_message = compose_kakao_message(selected_grouped)
    
    logger.info("부동산 인사이트 생성")
    insight = get_real_estate_insight(kakao_message)
    
    logger.info("Google Sheets에 저장")
    try:
        target_ws = sh.worksheet(TARGET_SHEET)
    except:
        target_ws = sh.add_worksheet(title=TARGET_SHEET, rows="100", cols="3")
        target_ws.append_row(["날짜", "요약", "부동산인사이트"])

    target_ws.append_row([today, kakao_message, insight], value_input_option='RAW')
    
    logger.info("데이터 저장 완료")
    log_execution_time(logger, start_time, 'daily_summary_and_insight')
    
    # 콘솔에도 출력
    print(kakao_message)

if __name__ == "__main__":
    main()
