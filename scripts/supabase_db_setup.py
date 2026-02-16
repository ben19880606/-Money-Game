#!/usr/bin/env python3
"""
Supabase Database Setup Script
設置 Money-Game 平台所需的數據庫表結構
"""

import os
import sys
from supabase import create_client, Client

# 環境變量
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")


def get_supabase_client() -> Client:
    """創建並返回 Supabase 客戶端"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("請設置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 環境變量")
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# SQL Queries for database setup

# 1. profiles 表 - 會員資料表
CREATE_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    membership_type VARCHAR(50) NOT NULL, -- borrower / lender
    payment_verified VARCHAR(10) DEFAULT 'NO', -- YES / NO
    payment_last_five_digits VARCHAR(10),
    payment_receipt_url TEXT,
    membership_tier VARCHAR(50), -- flagship / prestige / platinum
    activated_at TIMESTAMP,
    expires_at TIMESTAMP,
    line_id VARCHAR(255),
    line_user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# 2. loan_requests 表 - 借款案件表
CREATE_LOAN_REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS loan_requests (
    id SERIAL PRIMARY KEY,
    borrower_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    city VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending / active / completed / rejected / closed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES profiles(id) ON DELETE CASCADE
);
"""

# 3. lender_interactions 表 - 金主互動記錄表
CREATE_LENDER_INTERACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS lender_interactions (
    id SERIAL PRIMARY KEY,
    lender_id INT NOT NULL,
    request_id INT NOT NULL,
    interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_type VARCHAR(255), -- notification_sent / completed / rejected / viewed
    interaction_notes TEXT,
    FOREIGN KEY (lender_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES loan_requests(id) ON DELETE CASCADE
);
"""

# 4. 創建索引以提高查詢性能
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_profiles_membership_type ON profiles(membership_type);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_payment_verified ON profiles(payment_verified);",
    "CREATE INDEX IF NOT EXISTS idx_profiles_line_user_id ON profiles(line_user_id);",
    "CREATE INDEX IF NOT EXISTS idx_loan_requests_status ON loan_requests(status);",
    "CREATE INDEX IF NOT EXISTS idx_loan_requests_borrower_id ON loan_requests(borrower_id);",
    "CREATE INDEX IF NOT EXISTS idx_loan_requests_created_at ON loan_requests(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_lender_interactions_lender_id ON lender_interactions(lender_id);",
    "CREATE INDEX IF NOT EXISTS idx_lender_interactions_request_id ON lender_interactions(request_id);",
]


def execute_sql_via_rest_api(supabase: Client, sql: str, description: str):
    """
    使用 Supabase REST API 執行 SQL
    注意: 此函數需要使用 service_role key
    """
    try:
        print(f"執行: {description}...")
        # 注意: Supabase Python SDK 不直接支持執行原始 SQL
        # 在實際環境中，需要使用 Supabase SQL Editor 或 PostgREST 的 rpc 功能
        print(f"⚠️  請在 Supabase Dashboard 的 SQL Editor 中手動執行以下 SQL:")
        print("-" * 60)
        print(sql)
        print("-" * 60)
        print()
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    return True


def verify_tables(supabase: Client):
    """驗證表是否存在"""
    print("\n驗證數據庫表...")
    
    tables_to_check = ["profiles", "loan_requests", "lender_interactions"]
    
    for table in tables_to_check:
        try:
            # 嘗試查詢表（limit 0 不會返回數據）
            result = supabase.table(table).select("*").limit(0).execute()
            print(f"✅ 表 '{table}' 存在")
        except Exception as e:
            print(f"❌ 表 '{table}' 不存在或無法訪問: {e}")


def main():
    """主函數"""
    print("="*60)
    print("Money-Game 數據庫設置工具")
    print("="*60)
    print()
    
    try:
        supabase = get_supabase_client()
        print("✅ 成功連接到 Supabase\n")
        
        # 提示用戶
        print("⚠️  重要提示:")
        print("由於 Supabase Python SDK 的限制，以下 SQL 語句需要")
        print("在 Supabase Dashboard 的 SQL Editor 中手動執行。\n")
        
        # 輸出所有需要執行的 SQL
        print("="*60)
        print("請依次執行以下 SQL 語句：")
        print("="*60)
        print()
        
        print("-- 1. 創建 profiles 表")
        print(CREATE_PROFILES_TABLE)
        print()
        
        print("-- 2. 創建 loan_requests 表")
        print(CREATE_LOAN_REQUESTS_TABLE)
        print()
        
        print("-- 3. 創建 lender_interactions 表")
        print(CREATE_LENDER_INTERACTIONS_TABLE)
        print()
        
        print("-- 4. 創建索引")
        for i, index_sql in enumerate(CREATE_INDEXES, 1):
            print(f"-- 4.{i}")
            print(index_sql)
            print()
        
        # 驗證表
        verify_tables(supabase)
        
        print("\n" + "="*60)
        print("✅ 數據庫設置檢查完成")
        print("="*60)
        
    except ValueError as e:
        print(f"❌ 配置錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()