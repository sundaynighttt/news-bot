import os
import requests
import json
from datetime import datetime

class NotificationManager:
    """알림 관리자"""
    
    def __init__(self, script_name):
        self.script_name = script_name
        self.webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')  # 또는 SLACK_WEBHOOK_URL
        
    def send_error_notification(self, error_message, error_type="ERROR"):
        """에러 발생 시 알림 전송"""
        if not self.webhook_url:
            print("웹훅 URL이 설정되지 않았습니다.")
            return
            
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Discord 웹훅 형식
        data = {
            "embeds": [{
                "title": f"⚠️ {error_type}: {self.script_name}",
                "description": error_message,
                "color": 15158332 if error_type == "ERROR" else 16776960,  # 빨간색 또는 노란색
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "News Bot Alert"
                }
            }]
        }
        
        # Slack 웹훅 형식 (필요시 사용)
        # data = {
        #     "text": f"*{error_type}*: {self.script_name}",
        #     "attachments": [{
        #         "color": "danger" if error_type == "ERROR" else "warning",
        #         "fields": [{
        #             "title": "Error Details",
        #             "value": error_message,
        #             "short": False
        #         }],
        #         "ts": timestamp
        #     }]
        # }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"알림 전송 실패: {str(e)}")
    
    def send_success_notification(self, message):
        """성공 알림 전송"""
        if not self.webhook_url:
            return
            
        data = {
            "embeds": [{
                "title": f"✅ 성공: {self.script_name}",
                "description": message,
                "color": 3066993,  # 초록색
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "News Bot Alert"
                }
            }]
        }
        
        try:
            requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
        except:
            pass  # 성공 알림 실패는 무시
