"""
email_sender.py - Email sending module for member activation notifications.

Supports three email types:
1. Admin email (payment verification report)
2. User email (membership activation confirmation)
3. Finance email (invoice reminder)
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

ADMIN_EMAIL = "aijinetwork@gmail.com"
FINANCE_EMAIL = "qq0987811665qq@gmail.com"

PLAN_FEATURES = {
    "flagship": "文字廣告、私信聯絡",
    "prestige": "文字廣告、圖文廣告、私信聯絡",
    "platinum": "文字廣告、圖文廣告、私信聯絡、優先推薦",
}

PLAN_NAMES = {
    "flagship": "旗艦",
    "prestige": "尊榮",
    "platinum": "鉑金",
}


def _send_email(smtp_user: str, smtp_password: str, to_addr: str, subject: str, html_body: str) -> bool:
    """Send an HTML email via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info("✅ 郵件已發送至 %s", to_addr)
        return True
    except Exception as exc:
        logger.error("❌ 郵件發送失敗 (%s): %s", to_addr, exc)
        return False


def send_admin_email(smtp_user: str, smtp_password: str, order: dict, profile: dict) -> bool:
    """Send payment verification report to admin."""
    plan_code = order.get("plan_code", "")
    plan_name = PLAN_NAMES.get(plan_code, plan_code)
    reviewed_at = order.get("reviewed_at") or datetime.now(timezone.utc).isoformat()

    subject = f"[安心借貸網] 支付驗證報告 - 訂單 {order.get('order_no', order.get('id'))}"
    body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #2c7be5;">📋 支付驗證報告</h2>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%; max-width:600px;">
      <tr><th style="background:#f0f4ff; text-align:left;">訂單編號</th><td>{order.get('order_no', order.get('id', ''))}</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">用戶名稱</th><td>{profile.get('full_name', '')}</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">電話</th><td>{profile.get('phone', '')}</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">LINE ID</th><td>{profile.get('line_id', '')}</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">訂閱等級</th><td>{plan_name}（{plan_code}）</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">金額</th><td>NT$ {order.get('amount', '')}</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">有效期天數</th><td>{order.get('duration_days', '')} 天</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">匯款後五碼</th><td>{order.get('transfer_last5', '')}</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">發票載具編號</th><td>{order.get('carrier_number', '')}</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">審核狀態</th><td>✅ confirmed</td></tr>
      <tr><th style="background:#f0f4ff; text-align:left;">審核時間</th><td>{reviewed_at}</td></tr>
    </table>
    <p style="color:#888; font-size:12px; margin-top:24px;">此郵件由安心借貸網自動化系統發送，請勿回覆。</p>
    </body></html>
    """
    return _send_email(smtp_user, smtp_password, ADMIN_EMAIL, subject, body)


def send_user_email(smtp_user: str, smtp_password: str, order: dict, profile: dict, vip_until: str) -> bool:
    """Send membership activation confirmation to the user."""
    plan_code = order.get("plan_code", "")
    plan_name = PLAN_NAMES.get(plan_code, plan_code)
    features = PLAN_FEATURES.get(plan_code, "")
    user_email = profile.get("email", "")
    if not user_email:
        logger.warning("⚠️ 用戶郵件地址為空，跳過發送")
        return False

    # Format vip_until date for display
    try:
        expiry_display = datetime.fromisoformat(vip_until.replace("Z", "+00:00")).strftime("%Y 年 %m 月 %d 日")
    except Exception:
        expiry_display = vip_until

    subject = f"[安心借貸網] 🎉 您的會員資格已成功激活！"
    body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
    <div style="max-width:600px; margin:auto; border:1px solid #e0e0e0; border-radius:8px; overflow:hidden;">
      <div style="background:#2c7be5; padding:24px; text-align:center;">
        <h1 style="color:#fff; margin:0;">🎉 會員激活成功！</h1>
        <p style="color:#cce0ff; margin:8px 0 0;">安心借貸網 / axnihao.com</p>
      </div>
      <div style="padding:24px;">
        <p>親愛的 <strong>{profile.get('full_name', '會員')}</strong>，您好！</p>
        <p>感謝您選擇安心借貸網。您的訂閱已成功激活，現在可以享受以下服務：</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%; margin-top:12px;">
          <tr><th style="background:#f0f4ff; text-align:left;">訂閱等級</th><td><strong>{plan_name}</strong></td></tr>
          <tr><th style="background:#f0f4ff; text-align:left;">到期日</th><td><strong>{expiry_display}</strong></td></tr>
          <tr><th style="background:#f0f4ff; text-align:left;">包含功能</th><td>{features}</td></tr>
        </table>
        <p style="margin-top:20px;">如有任何問題，請隨時聯繫我們。</p>
        <p><a href="https://axnihao.com" style="color:#2c7be5;">前往安心借貸網</a></p>
      </div>
      <div style="background:#f8f9fa; padding:12px; text-align:center;">
        <p style="color:#888; font-size:12px; margin:0;">此郵件由安心借貸網自動化系統發送，請勿回覆。</p>
      </div>
    </div>
    </body></html>
    """
    return _send_email(smtp_user, smtp_password, user_email, subject, body)


def send_finance_email(smtp_user: str, smtp_password: str, order: dict, profile: dict) -> bool:
    """Send invoice issuance reminder to finance personnel."""
    plan_code = order.get("plan_code", "")
    plan_name = PLAN_NAMES.get(plan_code, plan_code)

    subject = f"[安心借貸網] 🧾 發票開立提醒 - 訂單 {order.get('order_no', order.get('id'))}"
    body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color:#e5762c;">🧾 發票開立提醒</h2>
    <p>以下訂單已確認付款，請盡快至發票平台開立發票：</p>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%; max-width:600px;">
      <tr><th style="background:#fff5ee; text-align:left;">訂單號</th><td>{order.get('order_no', order.get('id', ''))}</td></tr>
      <tr><th style="background:#fff5ee; text-align:left;">用戶名稱</th><td>{profile.get('full_name', '')}</td></tr>
      <tr><th style="background:#fff5ee; text-align:left;">訂閱等級</th><td>{plan_name}（{plan_code}）</td></tr>
      <tr><th style="background:#fff5ee; text-align:left;">金額</th><td>NT$ {order.get('amount', '')}</td></tr>
      <tr><th style="background:#fff5ee; text-align:left;">載具編號</th><td>{order.get('carrier_number', '')}</td></tr>
    </table>
    <p style="margin-top:20px;">
      👉 <a href="https://invoice.amego.tw/" style="color:#e5762c; font-weight:bold;">點此前往發票平台開立發票</a>
    </p>
    <p>開票完成後，請在後台確認已完成發票開立。</p>
    <p style="color:#888; font-size:12px; margin-top:24px;">此郵件由安心借貸網自動化系統發送，請勿回覆。</p>
    </body></html>
    """
    return _send_email(smtp_user, smtp_password, FINANCE_EMAIL, subject, body)


def send_all_activation_emails(smtp_user: str, smtp_password: str, order: dict, profile: dict, vip_until: str) -> dict:
    """Send all three activation emails and return a results dict."""
    results = {
        "admin": send_admin_email(smtp_user, smtp_password, order, profile),
        "user": send_user_email(smtp_user, smtp_password, order, profile, vip_until),
        "finance": send_finance_email(smtp_user, smtp_password, order, profile),
    }
    return results
