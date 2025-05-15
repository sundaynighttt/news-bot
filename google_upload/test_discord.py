#!/usr/bin/env python3
"""Discord 웹훅 테스트 스크립트"""

import os
from notification_utils import NotificationManager

def test_discord_webhook():
    # 테스트용 알림 매니저
    notifier = NotificationManager("테스트_스크립트")
    
    # 웹훅 URL 확인
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        print("다음 명령어로 설정하세요:")
        print('export DISCORD_WEBHOOK_URL="YOUR_WEBHOOK_URL"')
        return
    
    print(f"✅ 웹훅 URL이 설정되었습니다: {webhook_url[:50]}...")
    
    # 성공 알림 테스트
    print("\n📤 성공 알림 전송 중...")
    notifier.send_success_notification("테스트 성공! Discord 연결이 잘 되었습니다. 🎉")
    
    # 에러 알림 테스트
    print("📤 에러 알림 전송 중...")
    notifier.send_error_notification(
        "테스트 에러입니다. 실제 에러가 아닙니다!",
        error_type="WARNING"
    )
    
    print("\n✅ 테스트 완료! Discord 채널을 확인하세요.")

if __name__ == "__main__":
    test_discord_webhook()
