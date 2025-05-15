from datetime import datetime, timedelta

def get_kst_now():
    """한국 표준시(KST) 기준 현재 시간 반환"""
    return datetime.now() + timedelta(hours=9)

def get_kst_date():
    """한국 표준시(KST) 기준 현재 날짜 반환 (YYYY-MM-DD 형식)"""
    return get_kst_now().strftime('%Y-%m-%d')

def get_kst_date_with_weekday():
    """한국 표준시(KST) 기준 현재 날짜와 요일 반환 (MM/DD(요일) 형식)"""
    kst_now = get_kst_now()
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[kst_now.weekday()]
    return kst_now.strftime(f'%m/%d({weekday})')

def get_week_dates():
    """한국 표준시(KST) 기준 최근 7일간의 날짜 리스트 반환"""
    today = get_kst_now()
    return [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
