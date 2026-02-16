#!/usr/bin/env python3
"""
Simple Test Script for Money-Game Platform
簡單的測試腳本以驗證平台設置
"""

import os
import sys


def test_imports():
    """測試必需的 Python 模塊是否可導入"""
    print("測試 Python 模塊導入...")
    
    required_modules = [
        ('supabase', 'Supabase 客戶端'),
        ('requests', 'HTTP 請求庫'),
        ('dotenv', '環境變量加載'),
    ]
    
    failed = []
    
    for module, description in required_modules:
        try:
            __import__(module.replace('-', '_'))
            print(f"  ✅ {module}: {description}")
        except ImportError:
            print(f"  ❌ {module}: 無法導入")
            failed.append(module)
    
    return len(failed) == 0


def test_environment_variables():
    """測試環境變量是否設置"""
    print("\n測試環境變量...")
    
    required = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_CHANNEL_SECRET',
    ]
    
    optional = [
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'ALERT_EMAIL',
    ]
    
    missing = []
    
    print("\n  必需變量:")
    for var in required:
        if os.environ.get(var):
            print(f"    ✅ {var}")
        else:
            print(f"    ❌ {var}")
            missing.append(var)
    
    print("\n  可選變量:")
    for var in optional:
        if os.environ.get(var):
            print(f"    ✅ {var}")
        else:
            print(f"    ⚠️  {var}")
    
    return len(missing) == 0


def test_supabase_connection():
    """測試 Supabase 連接"""
    print("\n測試 Supabase 連接...")
    
    try:
        from supabase import create_client
        
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not key:
            print("  ⚠️  跳過: 缺少配置")
            return False
        
        supabase = create_client(url, key)
        
        # 嘗試查詢（不會返回數據）
        result = supabase.table("profiles").select("id").limit(0).execute()
        
        print("  ✅ 連接成功")
        return True
        
    except Exception as e:
        print(f"  ❌ 連接失敗: {e}")
        return False


def test_file_structure():
    """測試文件結構"""
    print("\n測試文件結構...")
    
    required_files = [
        'requirements.txt',
        'README.md',
        'DEPLOYMENT.md',
        'README_AUTOMATION.md',
        '.env.example',
        '.gitignore',
    ]
    
    required_dirs = [
        '.github/workflows',
        'scripts',
    ]
    
    required_workflows = [
        '.github/workflows/send-loan-notifications.yml',
        '.github/workflows/payment-auto-activation.yml',
        '.github/workflows/weekly-member-report.yml',
        '.github/workflows/security-monitor.yml',
        '.github/workflows/membership-expiration-reminder.yml',
        '.github/workflows/line-webhook-receiver.yml',
    ]
    
    # Note: The nested scripts/scripts/ directory structure is intentional
    # and matches the existing repository layout
    required_scripts = [
        'scripts/config_validator.py',
        'scripts/supabase_db_setup.py',
        'scripts/scripts/line_loan_notifier.py',
        'scripts/scripts/scripts/line_webhook_processor.py',
    ]
    
    all_ok = True
    
    print("\n  必需文件:")
    for file in required_files:
        if os.path.exists(file):
            print(f"    ✅ {file}")
        else:
            print(f"    ❌ {file}")
            all_ok = False
    
    print("\n  必需目錄:")
    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"    ✅ {dir}")
        else:
            print(f"    ❌ {dir}")
            all_ok = False
    
    print("\n  工作流文件:")
    for workflow in required_workflows:
        if os.path.exists(workflow):
            print(f"    ✅ {workflow}")
        else:
            print(f"    ❌ {workflow}")
            all_ok = False
    
    print("\n  腳本文件:")
    for script in required_scripts:
        if os.path.exists(script):
            print(f"    ✅ {script}")
        else:
            print(f"    ⚠️  {script}")
    
    return all_ok


def main():
    """主函數"""
    print("="*60)
    print("Money-Game 平台測試")
    print("="*60)
    print()
    
    # 嘗試加載 .env 文件
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 已加載 .env 文件\n")
    except ImportError:
        print("⚠️  python-dotenv 未安裝，跳過 .env 加載\n")
    except Exception:
        print("⚠️  未找到 .env 文件\n")
    
    # 運行所有測試
    tests = [
        ("模塊導入", test_imports),
        ("文件結構", test_file_structure),
        ("環境變量", test_environment_variables),
        ("Supabase 連接", test_supabase_connection),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ❌ 測試失敗: {e}")
            results.append((name, False))
    
    # 總結
    print("\n" + "="*60)
    print("測試結果總結")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n通過: {passed}/{total} 測試")
    
    if passed == total:
        print("\n✅ 所有測試通過!")
        sys.exit(0)
    else:
        print("\n❌ 部分測試失敗，請檢查配置")
        sys.exit(1)


if __name__ == "__main__":
    main()
