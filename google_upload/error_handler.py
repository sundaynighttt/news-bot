import functools
import traceback
from notification_utils import NotificationManager
from logging_config import setup_logger

def error_handler(script_name, notify_success=True):  # 기본값을 True로 변경
    """에러 처리 데코레이터
    
    Args:
        script_name: 스크립트 이름
        notify_success: 성공 시에도 알림을 보낼지 여부 (기본값: True)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger(script_name)
            notifier = NotificationManager(script_name)
            
            try:
                result = func(*args, **kwargs)
                
                # 성공 시 알림 (기본적으로 활성화)
                if notify_success:
                    notifier.send_success_notification(f"{script_name} 실행 완료 ✅")
                    
                return result
            except Exception as e:
                error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
                logger.error(error_msg)
                
                # 에러 알림 전송
                notifier.send_error_notification(
                    f"에러 발생: {str(e)}\n스크립트: {script_name}",
                    error_type="ERROR"
                )
                raise
                
        return wrapper
    return decorator
