#!/usr/bin/env python3
"""
Configuration Validation Script
驗證 Money-Game 平台的配置是否正確
"""

import os
import sys


def check_environment_variables():
    """檢查必需的環境變量"""
    print("檢查環境變量...")
    
    required_vars = {
        "SUPABASE_URL": "Supabase 項目 URL",
        "SUPABASE_SERVICE_ROLE_KEY": "Supabase Service Role Key",
        "LINE_CHANNEL_ACCESS_TOKEN": "LINE Channel Access Token",
        "LINE_CHANNEL_SECRET": "LINE Channel Secret",
    }
    
    optional_vars = {
        "SMTP_USERNAME": "SMTP 郵件用戶名（用於發送報告）",
        "SMTP_PASSWORD": "SMTP 郵件密碼",
        "ALERT_EMAIL": "告警郵箱地址",
    }
    
    missing_required = []
    missing_optional = []
    
    print("\n必需配置:")
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # 只顯示前幾個字符以保護隱私
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"  ✅ {var}: {masked_value}")
        else:
            print(f"  ❌ {var}: 未設置")
            missing_required.append((var, description))
    
    print("\n可選配置:")
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"  ✅ {var}: {masked_value}")
        else:
            print(f"  ⚠️  {var}: 未設置")
            missing_optional.append((var, description))
    
    return missing_required, missing_optional


def test_supabase_connection():
    """測試 Supabase 連接"""
    print("\n測試 Supabase 連接...")
    
    try:
        from supabase import create_client
        
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            print("  ⚠️  無法測試: 缺少 Supabase 配置")
            return False
        
        supabase = create_client(url, key)
        
        # 嘗試查詢 profiles 表
        result = supabase.table("profiles").select("id").limit(1).execute()
        print("  ✅ Supabase 連接成功")
        print(f"  ✅ profiles 表可訪問")
        
        # 嘗試查詢 loan_requests 表
        result = supabase.table("loan_requests").select("id").limit(1).execute()
        print(f"  ✅ loan_requests 表可訪問")
        
        # 嘗試查詢 lender_interactions 表
        result = supabase.table("lender_interactions").select("id").limit(1).execute()
        print(f"  ✅ lender_interactions 表可訪問")
        
        return True
        
    except ImportError:
        print("  ❌ 錯誤: 未安裝 supabase 庫")
        print("     請運行: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"  ❌ 連接失敗: {e}")
        return False


def test_line_api():
    """測試 LINE API 連接"""
    print("\n測試 LINE API 連接...")
    
    try:
        import requests
        
        token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        
        if not token:
            print("  ⚠️  無法測試: 缺少 LINE_CHANNEL_ACCESS_TOKEN")
            return False
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 測試 API 是否有效（使用 bot info endpoint）
        response = requests.get(
            "https://api.line.me/v2/bot/info",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("  ✅ LINE API 連接成功")
            bot_info = response.json()
            print(f"  ✅ Bot 名稱: {bot_info.get('displayName', '未知')}")
            return True
        else:
            print(f"  ❌ LINE API 連接失敗: HTTP {response.status_code}")
            print(f"     {response.text}")
            return False
            
    except ImportError:
        print("  ❌ 錯誤: 未安裝 requests 庫")
        return False
    except Exception as e:
        print(f"  ❌ 連接失敗: {e}")
        return False


def test_smtp_connection():
    """測試 SMTP 郵件配置"""
    print("\n測試 SMTP 郵件配置...")
    
    try:
        import smtplib
        
        username = os.environ.get("SMTP_USERNAME")
        password = os.environ.get("SMTP_PASSWORD")
        
        if not username or not password:
            print("  ⚠️  無法測試: 缺少 SMTP 配置")
            return False
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
            server.login(username, password)
            print("  ✅ SMTP 連接成功")
            print(f"  ✅ 郵箱: {username}")
            return True
            
    except smtplib.SMTPAuthenticationError:
        print("  ❌ SMTP 認證失敗: 用戶名或密碼錯誤")
        print("     如果使用 Gmail，請確保:")
        print("     1. 已啟用兩步驗證")
        print("     2. 使用應用專用密碼（而非帳戶密碼）")
        return False
    except Exception as e:
        print(f"  ❌ 連接失敗: {e}")
        return False


def check_dependencies():
    """檢查 Python 依賴"""
    print("\n檢查 Python 依賴...")
    
    required_packages = {
        "supabase": "Supabase 客戶端",
        "requests": "HTTP 請求庫",
        "python-dotenv": "環境變量加載",
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}: 已安裝")
        except ImportError:
            print(f"  ❌ {package}: 未安裝")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n  請運行以下命令安裝缺失的依賴:")
        print(f"  pip install -r requirements.txt")
    
    return len(missing_packages) == 0


def main():
    """主函數"""
    print("="*60)
    print("Money-Game 配置驗證工具")
    print("="*60)
    
    # 檢查依賴
    deps_ok = check_dependencies()
    
    # 檢查環境變量
    missing_required, missing_optional = check_environment_variables()
    
    # 運行連接測試
    supabase_ok = test_supabase_connection() if deps_ok else False
    line_ok = test_line_api() if deps_ok else False
    smtp_ok = test_smtp_connection() if deps_ok else False
    
    # 總結
    print("\n" + "="*60)
    print("驗證結果總結")
    print("="*60)
    
    if missing_required:
        print("\n❌ 缺少必需的環境變量:")
        for var, desc in missing_required:
            print(f"  - {var}: {desc}")
    
    if missing_optional:
        print("\n⚠️  缺少可選的環境變量:")
        for var, desc in missing_optional:
            print(f"  - {var}: {desc}")
    
    print("\n連接測試:")
    print(f"  {'✅' if supabase_ok else '❌'} Supabase 數據庫")
    print(f"  {'✅' if line_ok else '❌'} LINE Messaging API")
    print(f"  {'✅' if smtp_ok else '⚠️ '} SMTP 郵件服務（可選）")
    
    print("\n" + "="*60)
    
    if missing_required or not deps_ok or not supabase_ok or not line_ok:
        print("❌ 配置驗證失敗，請修復上述問題")
        sys.exit(1)
    else:
        print("✅ 配置驗證通過!")
        sys.exit(0)


if __name__ == "__main__":
    # 嘗試加載 .env 文件（如果存在）
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    main()
