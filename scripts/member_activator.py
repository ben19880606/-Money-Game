"""
member_activator.py - Core automation script for member activation.

Monitors bank_transfer_orders table for status changes from 'pending' to 'confirmed',
then automatically:
1. Updates the profiles table (plan_type, vip_until, carrier_number, transfer_last_5_digits)
2. Sends notification emails to admin, user, and finance personnel
"""

import os
import logging
from datetime import datetime, timedelta, timezone

from supabase import create_client, Client

from email_sender import send_all_activation_emails

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

PLAN_DURATION = {
    "flagship": 30,
    "prestige": 60,
    "platinum": 90,
}


def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_confirmed_orders(supabase: Client) -> list:
    """Fetch orders with status='confirmed' that are ready to be activated."""
    response = (
        supabase.table("bank_transfer_orders")
        .select(
            "id, user_id, plan_code, plan_name, amount, duration_days, "
            "transfer_last5, transfer_time, receipt_url, status, "
            "created_at, updated_at, reviewed_by, reviewed_at, review_note, "
            "order_no, carrier_number"
        )
        .eq("status", "confirmed")
        .execute()
    )
    orders = response.data or []
    logger.info("📋 找到 %d 筆已確認訂單", len(orders))
    return orders


def fetch_profile(supabase: Client, user_id: str) -> dict:
    """Fetch user profile by user_id."""
    response = (
        supabase.table("profiles")
        .select("id, full_name, phone, line_id, email, plan_type, vip_until")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return response.data or {}


def compute_vip_until(duration_days: int) -> str:
    """Calculate the new vip_until timestamp (UTC ISO 8601)."""
    return (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()


def activate_member(supabase: Client, order: dict) -> str | None:
    """Update profiles table and return the computed vip_until value."""
    user_id = order.get("user_id")
    if not user_id:
        logger.error("❌ 訂單 %s 缺少 user_id，跳過", order.get("id"))
        return None

    plan_code = order.get("plan_code", "")
    duration_days = order.get("duration_days") or PLAN_DURATION.get(plan_code, 30)
    vip_until = compute_vip_until(duration_days)

    update_data = {
        "plan_type": plan_code,
        "vip_until": vip_until,
        "carrier_number": order.get("carrier_number") or "",
        "transfer_last_5_digits": order.get("transfer_last5") or "",
    }

    supabase.table("profiles").update(update_data).eq("id", user_id).execute()
    logger.info(
        "✅ 用戶 %s 會員資格已更新：%s 至 %s",
        user_id,
        plan_code,
        vip_until,
    )
    return vip_until


def mark_order_processed(supabase: Client, order_id: str) -> None:
    """Mark the order as processed to avoid double-processing."""
    supabase.table("bank_transfer_orders").update(
        {"status": "activated"}
    ).eq("id", order_id).execute()
    logger.info("🔒 訂單 %s 狀態已更新為 activated", order_id)


def process_orders() -> None:
    """Main entry point: process all newly confirmed orders."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.error("❌ SMTP 憑證未設定，無法發送郵件")
        raise EnvironmentError("SMTP_USERNAME and SMTP_PASSWORD must be set.")

    supabase = get_supabase_client()
    orders = fetch_confirmed_orders(supabase)

    if not orders:
        logger.info("✅ 目前無需處理的訂單")
        return

    success_count = 0
    error_count = 0

    for order in orders:
        order_id = order.get("id")
        user_id = order.get("user_id")
        logger.info("🔄 處理訂單 %s（用戶 %s）", order_id, user_id)

        try:
            # Step 1: Update profile
            vip_until = activate_member(supabase, order)
            if not vip_until:
                error_count += 1
                continue

            # Step 2: Fetch full profile for email
            profile = fetch_profile(supabase, user_id)

            # Step 3: Send all notification emails
            email_results = send_all_activation_emails(
                SMTP_USERNAME, SMTP_PASSWORD, order, profile, vip_until
            )
            logger.info("📧 郵件發送結果: %s", email_results)

            # Step 4: Mark order as processed
            mark_order_processed(supabase, order_id)
            success_count += 1

        except Exception as exc:
            logger.exception("❌ 處理訂單 %s 時發生錯誤: %s", order_id, exc)
            error_count += 1

    logger.info(
        "🏁 完成！成功: %d 筆，失敗: %d 筆",
        success_count,
        error_count,
    )
    if error_count > 0:
        raise RuntimeError(f"{error_count} 筆訂單處理失敗，請查看日誌")


if __name__ == "__main__":
    process_orders()
