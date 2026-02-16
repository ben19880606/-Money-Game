# Money-Game 借貸媒介平台 🏦

<div align="center">

![Platform Status](https://img.shields.io/badge/status-active-success.svg)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**安全、高效的 P2P 借貸媒介平台自動化系統**

[網站地址](https://axnihao.com) • [部署指南](./DEPLOYMENT.md) • [自動化文檔](./README_AUTOMATION.md)

</div>

---

## 📋 目錄

- [平台簡介](#平台簡介)
- [核心功能](#核心功能)
- [技術架構](#技術架構)
- [快速開始](#快速開始)
- [工作流說明](#工作流說明)
- [會員等級](#會員等級)
- [數據庫結構](#數據庫結構)
- [安全性](#安全性)
- [維護與監控](#維護與監控)
- [常見問題](#常見問題)
- [貢獻指南](#貢獻指南)

---

## 平台簡介

Money-Game 是一個創新的 P2P 借貸媒介平台，連接有資金需求的借款人和提供資金的私人金主。平台提供：

### 🎯 對借款人
- ✅ **免費註冊** - 無需支付任何費用
- ✅ **快速發布** - 即時發布借款需求
- ✅ **自主管理** - 隨時開啟或關閉借款案件
- ✅ **隱私保護** - 僅顯示必要信息

### 💼 對金主（投資人）
- ✅ **優先通知** - 第一時間收到借款案件
- ✅ **LINE 集成** - 通過 LINE 接收即時通知
- ✅ **多級會員** - 三種會員等級可選
- ✅ **專屬服務** - 享受專業金融服務

---

## 核心功能

### 🤖 自動化工作流

| 工作流 | 功能 | 運行頻率 |
|--------|------|---------|
| **借款通知** | 自動推送新借款案件給金主 | 每小時 |
| **支付激活** | 自動激活已支付的金主會員 | 每小時 |
| **周報告** | 生成會員統計報告 | 每週一 |
| **安全監控** | 監控網站安全狀態 | 每 6 小時 |
| **到期提醒** | 提醒會員續約 | 每天 |
| **Webhook 處理** | 處理 LINE 用戶操作 | 實時 |

### 📱 LINE Bot 功能

- 📢 **即時通知** - 新借款案件推送
- 💬 **雙向互動** - 通過 LINE 標記案件狀態
- 🔔 **到期提醒** - 會員到期前 7 天提醒
- ✅ **案件管理** - 標記案件為已結案或拒絕

### 🔒 安全監控

- 🌐 **網站可用性** - 24/7 監控網站狀態
- 🔐 **SSL 證書** - 檢查證書有效期
- 🛡️ **內容檢查** - 偵測異常內容和攻擊跡象
- 📧 **即時告警** - 發現問題立即郵件通知

---

## 技術架構

```
┌─────────────────────────────────────────────┐
│      前端網站 (https://axnihao.com)         │
│  Readdy AI 平台 - 會員註冊、借款發布       │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│       Supabase 數據庫 (PostgreSQL)          │
│  ├─ profiles (會員資料)                    │
│  ├─ loan_requests (借款案件)               │
│  └─ lender_interactions (互動記錄)         │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│     GitHub Actions 自動化工作流             │
│  ├─ 借款通知 (每小時)                      │
│  ├─ 支付激活 (每小時)                      │
│  ├─ 周報告 (每週一)                        │
│  ├─ 安全監控 (每 6 小時)                   │
│  └─ 到期提醒 (每天)                        │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│      LINE Messaging API                     │
│  通知金主 + 接收操作反饋                    │
└─────────────────────────────────────────────┘
```

### 技術棧

- **後端**: Python 3.10+
- **數據庫**: Supabase (PostgreSQL)
- **自動化**: GitHub Actions
- **通訊**: LINE Messaging API
- **郵件**: SMTP (Gmail)
- **監控**: 自定義安全檢查腳本

---

## 快速開始

### 前置要求

- Python 3.10 或更高版本
- Git
- Supabase 帳號
- LINE Developers 帳號
- Gmail 帳號（用於報告）

### 安裝步驟

1. **克隆倉庫**

```bash
git clone https://github.com/ben19880606/-Money-Game.git
cd -Money-Game
```

2. **安裝依賴**

```bash
pip install -r requirements.txt
```

3. **配置環境變量**

```bash
cp .env.example .env
# 編輯 .env 文件，填入實際配置
```

4. **驗證配置**

```bash
python scripts/config_validator.py
```

5. **設置數據庫**

參考 [DEPLOYMENT.md](./DEPLOYMENT.md) 中的數據庫設置章節。

### 詳細部署指南

完整的部署步驟、配置說明和故障排查，請參閱 [DEPLOYMENT.md](./DEPLOYMENT.md)。

---

## 工作流說明

### 1️⃣ 借款通知工作流

**文件**: `.github/workflows/send-loan-notifications.yml`

**功能**:
- 每小時檢查新增的 pending 狀態借款
- 推送通知給所有已激活的金主會員
- 記錄通知發送歷史

**觸發條件**:
- 定時: 每小時自動執行
- 手動: 可通過 GitHub Actions 手動觸發

### 2️⃣ 支付自動激活工作流

**文件**: `.github/workflows/payment-auto-activation.yml`

**功能**:
- 檢查已填寫匯款信息的金主
- 自動更新 `payment_verified` 為 YES
- 設置 `activated_at` 時間戳
- 發送激活報告郵件

**觸發條件**:
- 定時: 每小時自動執行
- 手動: 可通過 GitHub Actions 手動觸發

### 3️⃣ 周報告工作流

**文件**: `.github/workflows/weekly-member-report.yml`

**功能**:
- 統計本週新會員數量
- 計算金主激活率
- 生成詳細報告並發送郵件

**觸發條件**:
- 定時: 每週一早上 8:00 UTC
- 手動: 可通過 GitHub Actions 手動觸發

### 4️⃣ 安全監控工作流

**文件**: `.github/workflows/security-monitor.yml`

**功能**:
- 檢查網站可用性和響應時間
- 驗證 SSL 證書有效期
- 偵測頁面異常內容
- 發現問題立即告警

**觸發條件**:
- 定時: 每 6 小時執行一次
- 手動: 可通過 GitHub Actions 手動觸發

### 5️⃣ 會員到期提醒工作流

**文件**: `.github/workflows/membership-expiration-reminder.yml`

**功能**:
- 檢查 7 天內到期的會員
- 通過 LINE 發送到期提醒
- 生成到期統計報告

**觸發條件**:
- 定時: 每天早上 9:00 UTC
- 手動: 可通過 GitHub Actions 手動觸發

### 6️⃣ LINE Webhook 處理工作流

**文件**: `.github/workflows/line-webhook-receiver.yml`

**功能**:
- 接收 LINE 用戶的操作
- 處理案件標記（已結案/拒絕）
- 更新數據庫狀態

**觸發條件**:
- Webhook: 通過 `repository_dispatch` 事件觸發
- 手動: 可通過 GitHub Actions 手動觸發

---

## 會員等級

### 借款人 (Borrower) - 免費

- ✅ 無限制發布借款案件
- ✅ 查看所有案件
- ✅ 自主管理案件狀態

### 金主 (Lender) - 付費會員

| 等級 | 中文名 | 價格 | 時長 | 功能 |
|------|--------|------|------|------|
| **Flagship** | 旗艦 | NT$ 50,000 | 30 天 | • LINE 即時通知<br>• 文字廣告<br>• 私信聯絡 |
| **Prestige** | 尊榮 | NT$ 75,000 | 60 天 | • 旗艦所有功能<br>• 圖文廣告<br>• 優先通知 |
| **Platinum** | 鉑金 | NT$ 100,000 | 90 天 | • 尊榮所有功能<br>• 優先推薦<br>• 專屬客服 |

---

## 數據庫結構

### profiles 表 (會員資料)

```sql
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    membership_type VARCHAR(50) NOT NULL, -- borrower / lender
    payment_verified VARCHAR(10) DEFAULT 'NO',
    payment_last_five_digits VARCHAR(10),
    membership_tier VARCHAR(50), -- flagship / prestige / platinum
    activated_at TIMESTAMP,
    expires_at TIMESTAMP,
    line_id VARCHAR(255),
    line_user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### loan_requests 表 (借款案件)

```sql
CREATE TABLE loan_requests (
    id SERIAL PRIMARY KEY,
    borrower_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    city VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES profiles(id)
);
```

### lender_interactions 表 (互動記錄)

```sql
CREATE TABLE lender_interactions (
    id SERIAL PRIMARY KEY,
    lender_id INT NOT NULL,
    request_id INT NOT NULL,
    interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_type VARCHAR(255),
    interaction_notes TEXT,
    FOREIGN KEY (lender_id) REFERENCES profiles(id),
    FOREIGN KEY (request_id) REFERENCES loan_requests(id)
);
```

---

## 安全性

### 🔒 數據保護

- ✅ 使用 Supabase service_role key（僅後端）
- ✅ 所有敏感配置存儲在 GitHub Secrets
- ✅ SSL/TLS 加密傳輸
- ✅ 定期安全掃描

### 🛡️ 訪問控制

- ✅ Row Level Security (RLS) 在 Supabase
- ✅ API 速率限制
- ✅ Webhook 簽名驗證
- ✅ 環境隔離

### 📊 監控告警

- ✅ 24/7 安全監控
- ✅ 異常行為偵測
- ✅ 自動郵件告警
- ✅ 詳細日誌記錄

---

## 維護與監控

### 日常監控

- 📈 **GitHub Actions**: 檢查工作流運行狀態
- 📧 **郵件報告**: 查看每週統計和告警
- 🔍 **Supabase**: 監控數據庫性能和存儲
- 📱 **LINE Bot**: 測試通知功能

### 定期維護

- 🔄 **每週**: 檢查工作流執行歷史
- 🔄 **每月**: 
  - 檢查數據庫大小和性能
  - 輪換 GitHub Secrets
  - 審查安全報告
- 🔄 **每季度**:
  - 更新依賴包版本
  - 審查和優化工作流
  - 備份重要數據

### 故障排查

遇到問題？查看以下資源：

1. [DEPLOYMENT.md](./DEPLOYMENT.md) - 完整的故障排查指南
2. [README_AUTOMATION.md](./README_AUTOMATION.md) - 工作流詳細說明
3. GitHub Actions 日誌 - 查看具體錯誤信息
4. `python scripts/config_validator.py` - 驗證配置

---

## 常見問題

### Q: 如何手動觸發工作流？

A: 前往 GitHub → Actions → 選擇工作流 → "Run workflow"

### Q: 為什麼金主收不到通知？

A: 檢查：
1. 金主的 `payment_verified` 是否為 YES
2. `line_user_id` 是否正確設置
3. LINE Channel Access Token 是否有效
4. 查看 GitHub Actions 日誌

### Q: 如何添加新的會員等級？

A: 修改以下位置：
1. 數據庫 `profiles` 表的 `membership_tier` 字段
2. 工作流中的會員等級判斷邏輯
3. 前端會員註冊頁面

### Q: 數據如何備份？

A: 
1. Supabase Dashboard → Database → Backup
2. 定期導出 SQL 轉儲
3. 保存重要郵件報告

---

## 貢獻指南

我們歡迎貢獻！如果您想為項目做出貢獻：

1. Fork 本倉庫
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 代碼規範

- 使用 Python 3.10+ 語法
- 遵循 PEP 8 編碼規範
- 添加必要的註釋和文檔
- 測試所有更改

---

## 授權

本項目採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件

---

## 聯繫方式

- **網站**: https://axnihao.com
- **郵箱**: aijinetwork@gmail.com
- **GitHub**: [@ben19880606](https://github.com/ben19880606)

---

<div align="center">

**由 ❤️ 打造 | Money-Game Team © 2026**

[⬆ 回到頂部](#money-game-借貸媒介平台-)

</div>
