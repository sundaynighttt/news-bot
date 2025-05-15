import os
import requests
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


def get_anthropic_headers() -> Dict[str, str]:
    """Anthropic API 헤더 반환
    
    Returns:
        Dict[str, str]: API 요청용 헤더
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
    
    return {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }


def get_claude_response(
    prompt: str,
    model: str = "claude-3-haiku-20240307",
    max_tokens: int = 100,
    temperature: float = 0.3,
    retry_count: int = 3
) -> str:
    """Claude API 호출 및 응답 반환
    
    Args:
        prompt: 프롬프트 텍스트
        model: 사용할 모델 (기본값: claude-3-haiku)
        max_tokens: 최대 토큰 수 (기본값: 100)
        temperature: 생성 온도 (기본값: 0.3)
        retry_count: 재시도 횟수 (기본값: 3)
        
    Returns:
        str: Claude의 응답 텍스트
    """
    headers = get_anthropic_headers()
    
    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    for i in range(retry_count):
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages", 
                headers=headers, 
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"].strip()
            else:
                logger.warning(f"API 요청 실패 (시도 {i+1}/{retry_count}): {response.status_code}")
                if i == retry_count - 1:
                    return f"API 요청 실패: {response.status_code}"
                    
        except requests.exceptions.Timeout:
            logger.warning(f"API 요청 타임아웃 (시도 {i+1}/{retry_count})")
            if i == retry_count - 1:
                return "API 요청 타임아웃"
                
        except Exception as e:
            logger.error(f"API 요청 중 오류 발생: {str(e)}")
            if i == retry_count - 1:
                return f"API 오류: {str(e)}"
    
    return "API 요청 실패"


def summarize_title(title: str, max_length: int = 25) -> str:
    """뉴스 제목 요약
    
    Args:
        title: 원본 제목
        max_length: 최대 길이 (기본값: 25)
        
    Returns:
        str: 요약된 제목
    """
    prompt = f"""다음 뉴스 제목을 {max_length}자 이내로 핵심만 요약하세요.

제목: {title}

규칙:
- {max_length}자 이내
- 불필요한 특수문자나 따옴표 제거
- 핵심 키워드와 주요 내용만 포함

예시:
입력: [단독] "이러다 삼성에 다 뺏긴다" '초유의 사태' 애플, 15년만에 내놓은 역대급 기능?
출력: 애플 나의찾기 15년만 국내 출시

요약:"""

    response = get_claude_response(prompt, max_tokens=50)
    
    # API 오류 시 원본 제목의 앞부분 반환
    if "API" in response or "오류" in response:
        clean_title = title.replace('"', '').replace("'", '').replace('[단독]', '').strip()
        return clean_title[:max_length]
    
    return response


def summarize_content(content: str, max_length: int = 20) -> str:
    """뉴스 내용 요약
    
    Args:
        content: 원본 내용
        max_length: 최대 길이 (기본값: 20)
        
    Returns:
        str: 요약된 내용
    """
    prompt = f"""다음 뉴스 내용의 핵심을 {max_length}자 이내로 요약하세요.

내용: {content[:500]}

규칙:
- {max_length}자 이내
- 핵심 사실이나 수치 포함
- 원인이나 영향 중심으로 요약

예시:
입력: 서울 강남구에서 20년 이상 보유한 아파트의 매도가 급증했다. 상급지로의 이동 수요와 절세 목적의 현금화가 주요 원인으로 분석된다.
출력: 상급지 이동과 절세 목적 현금화

요약:"""

    response = get_claude_response(prompt, max_tokens=50)
    
    # API 오류 시 기본 메시지 반환
    if "API" in response or "오류" in response:
        return "주요 내용 요약 실패"
    
    return response


def get_category_trend(items: List[tuple], max_items: int = 3) -> str:
    """카테고리별 핵심 트렌드 분석
    
    Args:
        items: (제목, 내용, 링크) 튜플 리스트
        max_items: 분석할 최대 항목 수 (기본값: 3)
        
    Returns:
        str: 트렌드 요약 텍스트
    """
    titles = [item[0] for item in items[:max_items]]
    
    prompt = f"""다음 뉴스들의 공통 트렌드를 15자 이내로 요약하세요.

{chr(10).join(titles)}

규칙:
- 15자 이내
- 하나의 간결한 문장
- 공통되는 핵심 주제 파악

요약:"""

    response = get_claude_response(prompt, max_tokens=30)
    
    # API 오류 시 기본 메시지 반환
    if "API" in response or "오류" in response:
        return "주요 동향"
    
    return response


def generate_real_estate_insight(text_block: str, model: str = "claude-3-sonnet-20240229") -> str:
    """부동산 인사이트 생성
    
    Args:
        text_block: 분석할 텍스트
        model: 사용할 모델 (기본값: claude-3-sonnet)
        
    Returns:
        str: 부동산 인사이트 텍스트
    """
    prompt = f"""너는 한국의 서울 아파트 투자 분석가야. 아래 뉴스 요약을 읽고, 서울아파트 투자 관점에서 의미 있는 시사점이나 트렌드를 5문단 이내로 정리해줘.

{text_block}

형식: 부동산 투자 관점에서 요약된 분석 문단 (5문단 이내)
"""

    return get_claude_response(
        prompt, 
        model=model,
        max_tokens=300,
        temperature=0.5
    )


def generate_weekly_summary(texts: str, model: str = "claude-3-haiku-20240307") -> str:
    """주간 요약 생성
    
    Args:
        texts: 요약할 텍스트들
        model: 사용할 모델 (기본값: claude-3-haiku)
        
    Returns:
        str: 주간 요약 텍스트
    """
    prompt = f"""아래는 이번 주의 주요 경제 뉴스 기사들입니다. 이 내용을 요약하여 아파트 투자자 입장에서 의미 있는 인사이트를 제시해주세요.
    
{texts}

요약:"""

    return get_claude_response(
        prompt,
        model=model,
        max_tokens=500,
        temperature=0.5
    )
