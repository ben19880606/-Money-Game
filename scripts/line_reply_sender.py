#!/usr/bin/env python3
"""
LINE Reply Sender - 使用 LINE Messaging API 發送 Push Message 給用戶

用途：
  - 發送 LINE 綁定成功確認訊息
  - 可作為獨立腳本在 GitHub Actions 中調用
"""

import os
import json
import requests

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_API_PUSH = "https://api.line.me/v2/bot/message/push"

BINDING_SUCCESS_MESSAGE = (
    "✅ 綁定成功！\n\n"
    "你已成功綁定安心借貸網官方帳號。\n\n"
    "從現在起，每當有新的借款案件時，我們會第一時間通知你。\n\n"
    "祝你投資愉快！"
)


def send_push_message(line_user_id: str, text: str) -> bool:
    """
    使用 LINE Messaging API 發送 Push Message。

    Args:
        line_user_id: 目標用戶的 LINE User ID
        text: 要發送的訊息文字

    Returns:
        True 如果發送成功，否則 False
    """
    try:
        message = {
            "to": line_user_id,
            "messages": [{"type": "text", "text": text}],
        }
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.post(LINE_API_PUSH, json=message, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ Message sent to {line_user_id}")
            return True
        print(f"❌ Failed to send message to {line_user_id}: {response.text}")
        return False
    except Exception as e:
        print(f"Error sending push message: {e}")
        return False


def send_binding_confirmation(line_user_id: str) -> bool:
    """發送 LINE 綁定成功確認訊息"""
    return send_push_message(line_user_id, BINDING_SUCCESS_MESSAGE)


if __name__ == "__main__":
    # 從環境變量讀取目標 LINE User ID（由 line_binding_handler 傳入）
    target_user_id = os.environ.get("LINE_TARGET_USER_ID", "")

    if not target_user_id:
        print("⚠️  LINE_TARGET_USER_ID not set. Using test user ID.")
        target_user_id = "U1234567890abcdef1234567890abcdef"

    success = send_binding_confirmation(target_user_id)
    if not success:
        exit(1)
