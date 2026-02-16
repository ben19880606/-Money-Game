# Money-Game 部署指南 (Deployment Guide)

## 📋 目錄

1. [前置要求](#前置要求)
2. [環境配置](#環境配置)
3. [GitHub Secrets 設置](#github-secrets-設置)
4. [數據庫設置](#數據庫設置)
5. [LINE Bot 配置](#line-bot-配置)
6. [本地開發](#本地開發)
7. [測試](#測試)
8. [部署驗證](#部署驗證)
9. [故障排查](#故障排查)

---

## 前置要求

### 必需的服務

- ✅ **GitHub 帳號** - 用於代碼託管和自動化工作流
- ✅ **Supabase 帳號** - 用於數據庫服務
- ✅ **LINE Developers 帳號** - 用於 LINE Bot 通知功能
- ✅ **Gmail 帳號** - 用於發送系統報告和告警（可選）

### 本地開發工具

- Python 3.10 或更高版本
- pip (Python 套件管理器)
- Git

---

## 環境配置

### 1. 克隆倉庫

```bash
git clone https://github.com/ben19880606/-Money-Game.git
cd -Money-Game
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 創建環境變量文件

複製示例文件並填入實際配置：

```bash
cp .env.example .env
```

編輯 `.env` 文件，填入以下配置：

```bash
# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# LINE Bot 配置
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# 郵件配置（可選）
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
ALERT_EMAIL=aijinetwork@gmail.com
```

---

## GitHub Secrets 設置

### 設置步驟

1. 前往 GitHub 倉庫
2. 點擊 **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **New repository secret**
4. 添加以下 Secrets：

| Secret 名稱 | 說明 | 如何獲取 |
|-----------|------|---------|
| `SUPABASE_URL` | Supabase 項目 URL | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key | Supabase Dashboard → Settings → API → service_role (⚠️ 保密) |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token | LINE Developers Console → 你的 Provider → 你的 Channel → Messaging API |
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | LINE Developers Console → 你的 Provider → 你的 Channel → Basic settings |
| `SMTP_USERNAME` | Gmail 郵箱地址 | 你的 Gmail 地址 |
| `SMTP_PASSWORD` | Gmail 應用密碼 | 見下方說明 |
| `ALERT_EMAIL` | 告警接收郵箱 | aijinetwork@gmail.com 或其他 |

### 獲取 Gmail 應用密碼

1. 啟用 Google 帳號的**兩步驗證**
   - 前往 https://myaccount.google.com/security
   - 啟用「兩步驗證」

2. 生成應用專用密碼
   - 前往 https://myaccount.google.com/apppasswords
   - 選擇「郵件」和「Windows 電腦」
   - 點擊「生成」
   - 複製 16 位密碼（去掉空格）

3. 將密碼保存到 `SMTP_PASSWORD` Secret

---

## 數據庫設置

### 1. 創建 Supabase 項目

1. 前往 [Supabase](https://supabase.com/)
2. 點擊 **New Project**
3. 填寫項目信息並創建

### 2. 執行 SQL 腳本

在 Supabase Dashboard 中：

1. 點擊左側菜單的 **SQL Editor**
2. 點擊 **New query**
3. 依次執行以下 SQL：

```sql
-- 1. 創建 profiles 表（會員資料表）
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

-- 2. 創建 loan_requests 表（借款案件表）
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

-- 3. 創建 lender_interactions 表（金主互動記錄表）
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

-- 4. 創建索引以提高性能
CREATE INDEX IF NOT EXISTS idx_profiles_membership_type ON profiles(membership_type);
CREATE INDEX IF NOT EXISTS idx_profiles_payment_verified ON profiles(payment_verified);
CREATE INDEX IF NOT EXISTS idx_profiles_line_user_id ON profiles(line_user_id);
CREATE INDEX IF NOT EXISTS idx_loan_requests_status ON loan_requests(status);
CREATE INDEX IF NOT EXISTS idx_loan_requests_borrower_id ON loan_requests(borrower_id);
CREATE INDEX IF NOT EXISTS idx_loan_requests_created_at ON loan_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_lender_interactions_lender_id ON lender_interactions(lender_id);
CREATE INDEX IF NOT EXISTS idx_lender_interactions_request_id ON lender_interactions(request_id);
```

### 3. 驗證數據庫設置

運行驗證腳本：

```bash
python scripts/supabase_db_setup.py
```

---

## LINE Bot 配置

### 1. 創建 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 創建新的 Provider（如果還沒有）
3. 在 Provider 下創建新的 Messaging API Channel
4. 填寫 Channel 信息

### 2. 配置 Messaging API

1. 在 Channel 的 **Messaging API** 標籤頁：
   - 點擊 **Issue** 生成 Channel Access Token
   - 複製 Token 並保存到 GitHub Secrets 的 `LINE_CHANNEL_ACCESS_TOKEN`
   
2. 在 **Basic settings** 標籤頁：
   - 複製 Channel Secret 並保存到 GitHub Secrets 的 `LINE_CHANNEL_SECRET`

3. 啟用必要功能：
   - 開啟 **Use webhooks**
   - 開啟 **Allow bot to join group chats**（如果需要）
   - 關閉 **Auto-reply messages**（避免干擾自定義回覆）

### 3. 獲取 LINE Bot 加入連結

1. 在 Messaging API 標籤頁找到 **QR code**
2. 用戶掃描 QR code 即可加入

---

## 本地開發

### 運行配置驗證

```bash
python scripts/config_validator.py
```

這將檢查：
- ✅ 所有必需的環境變量
- ✅ Supabase 連接
- ✅ LINE API 連接
- ✅ SMTP 郵件配置
- ✅ Python 依賴

### 測試 LINE 通知

```bash
# 測試發送借款通知
python scripts/scripts/line_loan_notifier.py
```

---

## 測試

### 手動觸發工作流

1. 前往 GitHub 倉庫的 **Actions** 標籤頁
2. 選擇要測試的工作流
3. 點擊 **Run workflow**
4. 選擇分支（通常是 `main`）
5. 點擊綠色的 **Run workflow** 按鈕

### 可測試的工作流

- ✅ **Send Loan Notifications** - 測試借款通知功能
- ✅ **Payment Auto-Activation** - 測試支付自動激活
- ✅ **Weekly Member Report** - 測試周報告生成
- ✅ **Security Monitor** - 測試安全監控
- ✅ **Membership Expiration Reminder** - 測試會員到期提醒

---

## 部署驗證

### 1. 檢查工作流狀態

1. 前往 **Actions** 標籤頁
2. 查看最近的工作流運行
3. 確保所有工作流都成功執行（綠色勾勾）

### 2. 驗證數據流

1. **創建測試借款案件**
   - 在 Supabase Dashboard 的 **Table Editor** 中
   - 在 `loan_requests` 表中插入測試數據

2. **驗證通知發送**
   - 等待下一個小時的自動運行
   - 或手動觸發 **Send Loan Notifications** 工作流
   - 檢查 LINE 是否收到通知

3. **驗證支付激活**
   - 在 `profiles` 表中創建測試金主
   - 設置 `payment_last_five_digits`
   - 觸發 **Payment Auto-Activation** 工作流
   - 檢查 `payment_verified` 是否更新為 `YES`

---

## 故障排查

### 問題 1: 工作流未執行

**可能原因：**
- GitHub Actions 未啟用
- 分支保護規則阻止運行
- Secrets 配置錯誤

**解決方法：**
1. 檢查 **Settings → Actions → General**
2. 確保 **Allow all actions and reusable workflows** 已啟用
3. 檢查所有 Secrets 是否正確配置

### 問題 2: Supabase 連接失敗

**可能原因：**
- `SUPABASE_URL` 或 `SUPABASE_SERVICE_ROLE_KEY` 錯誤
- Supabase 項目暫停或刪除
- 網絡問題

**解決方法：**
1. 驗證 Supabase URL 和 Key
2. 檢查 Supabase 項目狀態
3. 在本地運行 `python scripts/config_validator.py`

### 問題 3: LINE 通知未收到

**可能原因：**
- `LINE_CHANNEL_ACCESS_TOKEN` 過期或錯誤
- 用戶未加入 LINE Bot
- `line_user_id` 未正確保存

**解決方法：**
1. 驗證 LINE Token 是否有效
2. 確保用戶已掃描 QR code 加入
3. 檢查 `profiles` 表中的 `line_user_id` 字段

### 問題 4: 郵件未收到

**可能原因：**
- Gmail 應用密碼錯誤
- 未啟用兩步驗證
- 郵件被標記為垃圾郵件

**解決方法：**
1. 重新生成 Gmail 應用密碼
2. 檢查垃圾郵件文件夾
3. 在本地測試 SMTP 連接

### 查看詳細日誌

1. 前往 **Actions** 標籤頁
2. 點擊失敗的工作流運行
3. 點擊失敗的 Job
4. 展開每個步驟查看詳細輸出

---

## 維護建議

### 定期檢查

- 📅 每週檢查工作流運行狀態
- 📅 每月檢查 Supabase 數據庫大小
- 📅 每月檢查 LINE Bot 狀態
- 📅 每季度輪換 Secrets

### 監控指標

- 新會員註冊數
- 金主激活率
- 借款案件數
- 通知發送成功率
- 系統錯誤率

### 備份策略

1. **每週備份 Supabase 數據庫**
   - 使用 Supabase Dashboard 的 Backup 功能
   
2. **保存重要報告**
   - 週報告郵件
   - 安全監控報告

---

## 技術支持

如有問題，請：

1. 檢查本文檔的故障排查部分
2. 查看 GitHub Actions 的詳細日誌
3. 查看 [README_AUTOMATION.md](./README_AUTOMATION.md) 了解系統架構
4. 聯繫技術團隊：aijinetwork@gmail.com

---

**最後更新：2026-02-16**
