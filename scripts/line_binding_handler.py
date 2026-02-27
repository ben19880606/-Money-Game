#!/usr/bin/env python3
"""
LINE Binding Handler - 處理 LINE Webhook 回調，自動綁定用戶的 LINE User ID
當金主加入官方 LINE 帳號時，自動捕獲 LINE User ID 並更新 Supabase profiles 表
"""

import os
import json
import hmac
import hashlib
import base64
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
import requests
from supabase import create_client, Client

# 環境變量
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

LINE_OFFICIAL_ACCOUNT_ID = "@262sduyt"
LINE_API_PUSH = "https://api.line.me/v2/bot/message/push"
LINE_API_PROFILE = "https://api.line.me/v2/bot/profile/{user_id}"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def verify_line_signature(body: str, signature: str) -> bool:
    """驗證 LINE Webhook 簽名"""
    try:
        hash_object = hmac.new(
            LINE_CHANNEL_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        )
        expected_signature = base64.b64encode(hash_object.digest()).decode()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False


def get_line_user_profile(line_user_id: str) -> dict:
    """從 LINE API 獲取用戶詳細信息"""
    try:
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        }
        response = requests.get(
            LINE_API_PROFILE.format(user_id=line_user_id),
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        print(f"Failed to fetch LINE profile: {response.text}")
        return {}
    except Exception as e:
        print(f"Error fetching LINE user profile: {e}")
        return {}


def find_unbound_profile(line_user_id: str) -> dict | None:
    """
    在 Supabase 中查找未綁定 LINE User ID 的金主記錄。
    優先級：
      1. 找到 line_id = 官方帳號 且 line_user_id 為空的記錄
      2. 如只有一筆符合，直接綁定
    """
    try:
        response = (
            supabase.table("profiles")
            .select("id, email, line_id, line_user_id")
            .eq("line_id", LINE_OFFICIAL_ACCOUNT_ID)
            .is_("line_user_id", "null")
            .execute()
        )
        records = response.data or []

        if len(records) == 1:
            return records[0]
        if len(records) > 1:
            # 多筆未綁定記錄，無法自動確定，記錄日誌
            print(
                f"⚠️  Found {len(records)} unbound profiles for {LINE_OFFICIAL_ACCOUNT_ID}; "
                "cannot auto-bind without email verification."
            )
        return None
    except Exception as e:
        print(f"Error finding unbound profile: {e}")
        return None


def bind_line_user_id(profile_id: str, line_user_id: str) -> bool:
    """更新 profiles 表的 line_user_id、line_binding_status 和 line_binding_at"""
    try:
        supabase.table("profiles").update(
            {
                "line_user_id": line_user_id,
                "line_binding_status": "linked",
                "line_binding_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", profile_id).execute()
        print(f"✅ Profile {profile_id} bound to LINE User ID {line_user_id}")
        return True
    except Exception as e:
        print(f"Error binding LINE user ID: {e}")
        return False


def send_confirmation_email(to_email: str) -> bool:
    """發送 LINE 綁定確認郵件給用戶"""
    try:
        subject = "✅ 安心借貸網 LINE 綁定成功"
        body = (
            "親愛的會員，\n\n"
            "感謝你加入安心借貸網官方 LINE 帳號！\n\n"
            "你現在已成功綁定，我們會在以下情況第一時間通知你：\n"
            "✅ 有新的借款案件符合你的投資條件\n"
            "✅ 借款人已確認還款\n"
            "✅ 平台重要公告\n\n"
            "立即開始探索借款案件：https://axnihao.com/\n\n"
            "有任何問題，歡迎聯繫我們。\n\n"
            "祝你投資愉快！\n"
            "安心借貸網團隊"
        )
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USERNAME
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Confirmation email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False


def send_line_confirmation(line_user_id: str) -> bool:
    """透過 LINE Messaging API 發送綁定成功確認訊息"""
    try:
        message = {
            "to": line_user_id,
            "messages": [
                {
                    "type": "text",
                    "text": (
                        "✅ 綁定成功！\n\n"
                        "你已成功綁定安心借貸網官方帳號。\n\n"
                        "從現在起，每當有新的借款案件時，我們會第一時間通知你。\n\n"
                        "祝你投資愉快！"
                    ),
                }
            ],
        }
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.post(LINE_API_PUSH, json=message, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ LINE confirmation sent to {line_user_id}")
            return True
        print(f"❌ LINE message failed: {response.text}")
        return False
    except Exception as e:
        print(f"Error sending LINE confirmation: {e}")
        return False


def process_follow_event(event: dict) -> bool:
    """
    處理用戶加入官方帳號 (follow) 事件：
      1. 提取 LINE User ID
      2. 查詢 Supabase 找到對應未綁定的金主
      3. 更新 line_user_id、line_binding_status、line_binding_at
      4. 發送確認郵件和 LINE 訊息
    """
    try:
        line_user_id = event["source"]["userId"]
        print(f"🔗 Follow event from LINE User ID: {line_user_id}")

        profile = find_unbound_profile(line_user_id)
        if not profile:
            # 無匹配記錄，仍發送歡迎訊息
            send_line_confirmation(line_user_id)
            print("ℹ️  No matching unbound profile found; welcome message sent.")
            return True

        profile_id = profile["id"]
        email = profile.get("email")

        if not bind_line_user_id(profile_id, line_user_id):
            return False

        # 發送確認郵件（如果有 email）
        if email and SMTP_USERNAME and SMTP_PASSWORD:
            send_confirmation_email(email)

        # 發送 LINE 確認訊息
        send_line_confirmation(line_user_id)
        return True

    except Exception as e:
        print(f"Error processing follow event: {e}")
        return False


def process_webhook_payload(body: str, signature: str) -> dict:
    """
    驗證並處理 LINE Webhook payload。
    返回 HTTP 狀態碼與回應主體的字典。
    """
    if not verify_line_signature(body, signature):
        print("❌ 簽名驗證失敗")
        return {"statusCode": 403, "body": json.dumps({"message": "Forbidden"})}

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON payload: {e}")
        return {"statusCode": 400, "body": json.dumps({"message": "Bad Request"})}

    events = payload.get("events", [])
    for event in events:
        event_type = event.get("type")
        if event_type == "follow":
            process_follow_event(event)
        elif event_type == "postback":
            print(f"ℹ️  Postback event received (not handled by binding handler)")
        elif event_type == "message":
            print(f"ℹ️  Message event received (not handled by binding handler)")

    return {"statusCode": 200, "body": json.dumps({"message": "OK"})}


if __name__ == "__main__":
    # 從 GitHub Actions 環境變量讀取 Webhook payload
    webhook_body = os.environ.get("LINE_WEBHOOK_BODY", "")
    webhook_signature = os.environ.get("LINE_WEBHOOK_SIGNATURE", "")

    if not webhook_body:
        # 本地測試用的示例 payload
        webhook_body = json.dumps(
            {
                "events": [
                    {
                        "type": "follow",
                        "source": {"userId": "U1234567890abcdef1234567890abcdef"},
                        "timestamp": 1677123456789,
                    }
                ]
            }
        )
        print("⚠️  Using test payload (no LINE_WEBHOOK_BODY provided)")

    result = process_webhook_payload(webhook_body, webhook_signature)
    print(f"Result: {result}")
