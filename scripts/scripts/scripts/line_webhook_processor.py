#!/usr/bin/env python3
"""
Line Webhook Processor - 处理金主从 LINE 发来的操作（已結案/拒絕）
"""

import os
import json
import hmac
import hashlib
from datetime import datetime
import requests
from supabase import create_client, Client

# 环境变量
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_line_signature(body, signature):
    """验证 LINE 消息签名"""
    try:
        hash_object = hmac.new(
            LINE_CHANNEL_SECRET.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        )
        expected_signature = hash_object.digest()
        expected_signature_b64 = hash_object.hexdigest()
        
        # LINE 的签名验证方式
        return hmac.compare_digest(signature, expected_signature_b64)
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False

def get_lender_id_from_line_user(line_user_id):
    """通过 LINE User ID 获取金主 ID"""
    try:
        response = supabase.table("profiles").select("id").or_(
            f"line_id.eq.{line_user_id},line_user_id.eq.{line_user_id}"
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        print(f"Error getting lender ID: {e}")
        return None

def update_loan_status(loan_id, new_status, lender_id, action_data):
    """更新借款状态"""
    try:
        # 更新 loan_requests 表
        supabase.table("loan_requests").update(
            {"status": new_status}
        ).eq("id", loan_id).execute()
        
        # 在 lender_interactions 表中记录操作
        supabase.table("lender_interactions").insert({
            "lender_id": lender_id,
            "request_id": loan_id,
            "interaction_type": new_status,
            "interaction_date": datetime.utcnow().isoformat(),
            "interaction_notes": json.dumps(action_data)
        }).execute()
        
        print(f"✅ 借款 #{loan_id} 已更新为 {new_status}")
        return True
    except Exception as e:
        print(f"Error updating loan status: {e}")
        return False

def send_line_reply(line_user_id, message_text):
    """发送 LINE 回复消息"""
    try:
        message = {
            "to": line_user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message_text
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.line.me/v2/bot/message/push",
            json=message,
            headers=headers
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending LINE reply: {e}")
        return False

def process_postback_action(event):
    """处理 LINE postback 事件（按钮点击）"""
    try:
        line_user_id = event["source"]["userId"]
        postback_data = event["postback"]["data"]
        
        # 解析 postback 数据
        # 格式：action=completed&loan_id=123
        params = {}
        for param in postback_data.split("&"):
            key, value = param.split("=")
            params[key] = value
        
        action = params.get("action")  # completed or rejected
        loan_id = int(params.get("loan_id"))
        
        # 获取金主 ID
        lender_id = get_lender_id_from_line_user(line_user_id)
        if not lender_id:
            print(f"❌ 无法找到金主 ID: {line_user_id}")
            return False
        
        # 映射 action 到 status
        status_map = {
            "completed": "completed",
            "rejected": "rejected"
        }
        
        new_status = status_map.get(action)
        if not new_status:
            print(f"❌ 未知的操作: {action}")
            return False
        
        # 更新状态
        update_loan_status(loan_id, new_status, lender_id, {
            "line_user_id": line_user_id,
            "action": action
        })
        
        # 发送确认消息
        if action == "completed":
            reply_message = f"✅ 案件 #{loan_id} 已標記為已結案\n\n感謝您的配合！"
        else:
            reply_message = f"❌ 案件 #{loan_id} 已標記為拒絕\n\n感謝您的反饋！"
        
        send_line_reply(line_user_id, reply_message)
        
        return True
    except Exception as e:
        print(f"Error processing postback action: {e}")
        return False

def process_message_event(event):
    """处理文字消息事件"""
    try:
        message_text = event["message"].get("text", "").lower()
        line_user_id = event["source"]["userId"]
        
        # 简单的关键词匹配
        if "結案" in message_text or "完成" in message_text:
            # 用户想标记为已結案
            # 实际应用中需要更复杂的逻辑来识别是哪个案件
            reply = "您想標記哪個案件為已結案？請點擊通知中的按鈕進行操作。"
        elif "拒絕" in message_text:
            reply = "您想拒絕哪個案件？請點擊通知中的按鈕進行操作。"
        else:
            reply = "感謝您的消息！若要標記案件的狀態，請點擊通知中的按鈕。"
        
        send_line_reply(line_user_id, reply)
        return True
    except Exception as e:
        print(f"Error processing message event: {e}")
        return False

def lambda_handler(event, context):
    """AWS Lambda 或 Supabase Function 处理程序"""
    try:
        # 获取请求体和签名
        body = json.dumps(event.get("body", {})) if isinstance(event.get("body"), dict) else event.get("body", "{}")
        signature = event.get("headers", {}).get("x-line-signature", "")
        
        # 验证签名
        if not verify_line_signature(body, signature):
            print("❌ 签名验证失败")
            return {"statusCode": 403, "body": json.dumps({"message": "Forbidden"})}
        
        # 解析事件
        events = json.loads(body).get("events", [])
        
        for event in events:
            event_type = event.get("type")
            
            if event_type == "postback":
                # 处理按钮点击事件
                process_postback_action(event)
            elif event_type == "message":
                # 处理文字消息
                process_message_event(event)
            elif event_type == "follow":
                # 用户关注官方账号
                line_user_id = event["source"]["userId"]
                send_line_reply(line_user_id, "感謝您關注安心借貸網官方帳號！我們會定期為您推送新的借款案件。")
        
        return {"statusCode": 200, "body": json.dumps({"message": "OK"})}
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {"statusCode": 500, "body": json.dumps({"message": "Internal Server Error"})}

# 用于本地测试
if __name__ == "__main__":
    test_event = {
        "body": json.dumps({
            "events": [
                {
                    "type": "postback",
                    "source": {"userId": "U1234567890abcdef1234567890abcdef"},
                    "postback": {"data": "action=completed&loan_id=123"}
                }
            ]
        }),
        "headers": {"x-line-signature": "test_signature"}
    }
    
    result = lambda_handler(test_event, None)
    print(result)
