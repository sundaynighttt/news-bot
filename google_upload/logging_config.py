import logging
import os
from datetime import datetime

def setup_logger(script_name):
    """각 스크립트용 로거 설정"""
    # 로그 디렉토리 생성
    log_dir = os.path.join(os.path.dirname(__file__), 'logs', datetime.now().strftime('%Y-%m'))
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일 경로
    log_file = os.path.join(log_dir, f"{script_name}_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 로거 설정
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷터
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_execution_time(logger, start_time, script_name):
    """실행 시간 로깅"""
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    logger.info(f"{script_name} 실행 완료 - 소요시간: {execution_time:.2f}초")
