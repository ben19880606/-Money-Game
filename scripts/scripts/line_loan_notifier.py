#!/usr/bin/env python3
"""
Line Loan Notifier - 每小时检查新借款并发送 LINE 通知给金主会员
"""

import os
import json
from datetime import datetime, timedelta
import requests
from supabase import create_client, Client

# 环境变量
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
LINE_API_ENDPOINT = "https://api.line.me/v2/bot/message/push"

def get_new_loan_requests():
    """获取最近1小时新增的 pending 状态借款"""
    try:
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        response = supabase.table("loan_requests").select(
            "id, title, amount, description, city, borrower_id, created_at"
        ).eq(
            "status", "pending"
        ).gte(
            "created_at", one_hour_ago
        ).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching loan requests: {e}")
        return []

def get_lender_members():
    """获取所有金主会员及其 LINE ID"""
    try:
        response = supabase.table("profiles").select(
            "id, line_id, line_user_id, membership_type"
        ).in_(
            "membership_type", ["lender", "旗艦", "尊榮", "鉑金"]
        ).eq(
            "payment_verified", "YES"
        ).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching lender members: {e}")
        return []

def send_line_notification(line_user_id, loan_data):
    """发送 LINE 私訊通知给金主"""
    try:
        message = {
            "to": line_user_id,
            "messages": [
                {
                    "type": "text",
                    "text": f"【安心借貸網 | 新借款案件】\n\n"
                           f"案件編號：LR{loan_data['id']}\n"
                           f"借款金額：${loan_data['amount']:,}\n"
                           f"地區：{loan_data['city']}\n"
                           f"用途：{loan_data['description']}"
                },
                {
                    "type": "template",
                    "altText": "新借款案件",
                    "template": {
                        "type": "buttons",
                        "text": "點擊下方按���查看完整信息",
                        "actions": [
                            {
                                "type": "uri",
                                "label": "立即查看",
                                "uri": f"https://axnihao.com/loan/{loan_data['id']}"
                            }
                        ]
                    }
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(LINE_API_ENDPOINT, json=message, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 通知已发送给 {line_user_id}")
            return True
        else:
            print(f"❌ 发送失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending LINE notification: {e}")
        return False

def record_notification_sent(loan_id, lender_id):
    """记录通知发送记录"""
    try:
        supabase.table("lender_interactions").insert({
            "lender_id": lender_id,
            "request_id": loan_id,
            "interaction_type": "notification_sent",
            "interaction_date": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"Error recording notification: {e}")

def main():
    """主函数"""
    print(f"🔄 开始检查新借款... [{datetime.now().isoformat()}]")
    
    # 获取新借款
    loans = get_new_loan_requests()
    print(f"📋 找到 {len(loans)} 笔新借款")
    
    if not loans:
        print("✅ 没有新借款")
        return
    
    # 获取所有金主会员
    lenders = get_lender_members()
    print(f"👥 找到 {len(lenders)} 个金主会员")
    
    if not lenders:
        print("⚠️  没有有效的金主会员")
        return
    
    # 发送通知给每个金主
    notification_count = 0
    for loan in loans:
        for lender in lenders:
            # 优先使用 line_user_id，如果没有则使用 line_id
            line_id = lender.get("line_user_id") or lender.get("line_id")
            
            if line_id and send_line_notification(line_id, loan):
                record_notification_sent(loan["id"], lender["id"])
                notification_count += 1
    
    print(f"\n✅ 任务完成! 发送了 {notification_count} 条通知")

if __name__ == "__main__":
    main()
