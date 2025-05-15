from datetime import datetime, timedelta
from typing import List, Optional


def get_kst_now() -> datetime:
    """한국 표준시(KST) 기준 현재 시간 반환
    
    Returns:
        datetime: KST 기준 현재 시간
    """
    return datetime.now() + timedelta(hours=9)


def get_kst_date() -> str:
    """한국 표준시(KST) 기준 현재 날짜 반환
    
    Returns:
        str: YYYY-MM-DD 형식의 날짜 문자열
    """
    return get_kst_now().strftime('%Y-%m-%d')


def get_kst_date_with_weekday() -> str:
    """한국 표준시(KST) 기준 현재 날짜와 요일 반환
    
    Returns:
        str: MM/DD(요일) 형식의 날짜 문자열
    """
    kst_now = get_kst_now()
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[kst_now.weekday()]
    return kst_now.strftime(f'%m/%d({weekday})')


def get_week_dates() -> List[str]:
    """한국 표준시(KST) 기준 최근 7일간의 날짜 리스트 반환
    
    Returns:
        List[str]: YYYY-MM-DD 형식의 날짜 문자열 리스트
    """
    today = get_kst_now()
    return [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]


def get_year_month_path() -> str:
    """현재 연도/월 경로 반환 (파일 저장용)
    
    Returns:
        str: YYYY/MM 형식의 경로 문자열
    """
    return get_kst_now().strftime('%Y/%m')


def is_weekend() -> bool:
    """현재 날짜가 주말인지 확인
    
    Returns:
        bool: 토요일(5) 또는 일요일(6)이면 True
    """
    return get_kst_now().weekday() in [5, 6]


def get_formatted_datetime() -> str:
    """로그용 포맷된 현재 시간 반환
    
    Returns:
        str: YYYY-MM-DD HH:MM:SS 형식의 시간 문자열
    """
    return get_kst_now().strftime('%Y-%m-%d %H:%M:%S')
