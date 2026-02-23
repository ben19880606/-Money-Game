# LINE OAuth 綁定設置指南

本文檔說明如何配置一鍵 LINE 官方帳號綁定系統，讓金主會員可以在安心借貸網自動接收借款通知。

## 系統概覽

```
金主在網站點擊 [綁定 LINE] 按鈕
  ↓
跳轉到 LINE 官方帳號頁面（line.me/R/ti/p/@262sduyt）
  ↓
金主點「加入」
  ↓
LINE 伺服器發送 follow Webhook 到 GitHub Actions
  ↓
line-oauth-binding.yml 觸發 → 執行 scripts/line_binding_handler.py
  ↓
驗證簽名 → 查詢 Supabase → 更新 profiles.line_user_id
  ↓
發送確認 LINE 訊息 + 確認郵件
  ↓
完成！金主自動接收借款通知
```

---

## 1. LINE Developers 後台配置

### 1.1 前往 LINE Developers Console

1. 開啟 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇你的 Provider
3. 點擊 **Messaging API Channel**（Channel ID: `2008566543`）

### 1.2 設置 Webhook URL

在 **Messaging API** 標籤頁：

1. 找到 **Webhook settings**
2. 將 **Webhook URL** 設為：
   ```
   https://smee.io/<your-smee-channel>
   ```
   > **說明：** LINE Webhook 需要公開的 HTTPS URL。由於 GitHub Actions 無法直接作為 HTTP 伺服器，
   > 建議使用 [Smee.io](https://smee.io) 或 [ngrok](https://ngrok.com) 作為中繼，
   > 將 LINE Webhook 轉發為 GitHub `repository_dispatch` 事件。
   >
   > 另一方案是使用 Supabase Edge Function 或 Cloudflare Worker 作為 Webhook 接收端，
   > 再呼叫 GitHub API 觸發 `repository_dispatch`。

3. 點擊 **Verify** 確認 URL 可達（應返回 200）
4. 開啟 **Use webhook** 開關

### 1.3 訂閱事件類型

確保以下事件已啟用：

| 事件 | 說明 |
|------|------|
| ✅ Follow | 用戶加入官方帳號（**必須**，用於自動綁定） |
| ✅ Message | 用戶發送訊息 |
| ✅ Join | Bot 加入群組 |
| ✅ Leave | Bot 離開群組 |

### 1.4 取得 Channel Access Token

1. 在 **Messaging API** 頁面，找到 **Channel access token**
2. 點擊 **Issue** 生成長效 Token
3. 複製 Token，稍後添加到 GitHub Secrets

---

## 2. GitHub Secrets 配置

前往 GitHub 倉庫 → **Settings** → **Secrets and variables** → **Actions**，新增以下 Secrets：

| Secret 名稱 | 說明 | 範例值 |
|------------|------|--------|
| `LINE_CHANNEL_ID` | LINE Channel ID | `2008566543` |
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | （從 LINE Developers 後台取得） |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token | （從 LINE Developers 後台 Issue） |
| `SUPABASE_URL` | Supabase 專案 URL | `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key | （從 Supabase 後台取得） |
| `SMTP_USERNAME` | Gmail 帳號 | `your@gmail.com` |
| `SMTP_PASSWORD` | Gmail App 密碼 | （需開啟兩步驟驗證並生成 App 密碼） |
| `ALERT_EMAIL` | 接收告警郵件的地址 | `admin@axnihao.com` |

> ⚠️ **安全注意事項：** 切勿將 Channel Secret 或任何 Token 直接寫入程式碼或提交到版本庫。
> 所有敏感信息必須透過 GitHub Secrets 管理。

---

## 3. Supabase 資料庫配置

確保 `profiles` 表包含以下欄位（如不存在，請在 Supabase SQL Editor 執行）：

```sql
-- 添加 LINE 綁定相關欄位（如果尚未存在）
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS line_user_id TEXT,
  ADD COLUMN IF NOT EXISTS line_binding_status TEXT DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS line_binding_at TIMESTAMPTZ;

-- 建議加上索引以加快查詢
CREATE INDEX IF NOT EXISTS idx_profiles_line_user_id ON profiles(line_user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_line_binding_status ON profiles(line_binding_status);
```

### 欄位說明

| 欄位 | 類型 | 說明 |
|------|------|------|
| `line_id` | TEXT | 金主填寫的 LINE ID（如 `@262sduyt`） |
| `line_user_id` | TEXT | 系統自動捕獲的 LINE User ID（如 `U1234...`） |
| `line_binding_status` | TEXT | `pending` / `linked` |
| `line_binding_at` | TIMESTAMPTZ | 綁定完成時間 |

---

## 4. 前端按鈕實現

在金主的個人設定頁面，添加綁定按鈕：

```html
<a href="https://line.me/R/ti/p/@262sduyt" target="_blank" rel="noopener noreferrer">
  <button>綁定 LINE 官方帳號</button>
</a>
```

或使用 JavaScript：

```javascript
function bindLineAccount() {
  window.open('https://line.me/R/ti/p/@262sduyt', '_blank');
}
```

---

## 5. Webhook 中繼設置（推薦方案：Supabase Edge Function）

由於 GitHub Actions 無法直接接收 HTTP 請求，需要一個中繼服務：

### 5.1 建立 Supabase Edge Function

```typescript
// supabase/functions/line-webhook/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

const GITHUB_TOKEN = Deno.env.get('GITHUB_TOKEN')
const REPO_OWNER = 'ben19880606'
const REPO_NAME = '-Money-Game'

serve(async (req) => {
  const body = await req.text()
  const signature = req.headers.get('x-line-signature') || ''

  // 轉發到 GitHub Actions repository_dispatch
  const response = await fetch(
    `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/dispatches`,
    {
      method: 'POST',
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json',
      },
      body: JSON.stringify({
        event_type: 'line_follow_event',
        client_payload: {
          body: body,
          signature: signature,
        },
      }),
    }
  )

  return new Response('OK', { status: 200 })
})
```

### 5.2 部署 Edge Function

```bash
supabase functions deploy line-webhook
```

### 5.3 配置 LINE Webhook URL

將 Webhook URL 設為 Edge Function 的 URL：
```
https://<your-project-ref>.supabase.co/functions/v1/line-webhook
```

---

## 6. 測試流程

### 6.1 本地測試

```bash
# 安裝依賴
pip install supabase requests python-dotenv

# 設置環境變量
export SUPABASE_URL="https://xxxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export LINE_CHANNEL_SECRET="your-channel-secret"
export LINE_CHANNEL_ACCESS_TOKEN="your-access-token"

# 運行綁定處理腳本（使用測試 payload）
python scripts/line_binding_handler.py

# 測試發送 LINE 訊息
export LINE_TARGET_USER_ID="U1234567890abcdef"
python scripts/line_reply_sender.py
```

### 6.2 LINE Developers Webhook Tester

1. 前往 LINE Developers Console → Messaging API
2. 找到 **Webhook settings** → 點擊 **Verify**
3. 確認返回 `{"message": "OK"}`

### 6.3 手動觸發 GitHub Actions

1. 前往 GitHub 倉庫 → **Actions** → **LINE OAuth Binding**
2. 點擊 **Run workflow**
3. 在 `webhook_body` 輸入測試 JSON：
   ```json
   {"events":[{"type":"follow","source":{"userId":"U1234567890abcdef1234567890abcdef"},"timestamp":1677123456789}]}
   ```
4. 確認 workflow 正常執行

---

## 7. 故障排查

### 問題：Webhook 驗證失敗（403 Forbidden）

**原因：** LINE Channel Secret 不正確，或請求體被修改  
**解決：** 確認 `LINE_CHANNEL_SECRET` GitHub Secret 與 LINE Developers 後台的值完全一致

### 問題：找不到匹配的金主記錄

**原因：** `profiles.line_id` 未設為 `@262sduyt`，或已有其他記錄綁定  
**解決：** 確認用戶在填寫資料時，`line_id` 欄位設為官方帳號 ID `@262sduyt`

### 問題：LINE 確認訊息未收到

**原因：** `LINE_CHANNEL_ACCESS_TOKEN` 過期或不正確  
**解決：** 前往 LINE Developers Console 重新 Issue Channel Access Token，並更新 GitHub Secret

### 問題：郵件未收到

**原因：** Gmail App 密碼未設置，或 SMTP 設定錯誤  
**解決：**
1. 前往 Google 帳號設定 → 安全性 → 兩步驟驗證
2. 生成 App 密碼（選擇「Mail」和「Other」）
3. 更新 `SMTP_PASSWORD` GitHub Secret

---

## 8. 相關文件

- `scripts/line_binding_handler.py` — 處理 LINE follow 事件，自動綁定用戶
- `scripts/line_reply_sender.py` — 發送 LINE Push Message
- `scripts/scripts/scripts/line_webhook_processor.py` — 處理 postback 和 message 事件（現有檔案，路徑為倉庫原始結構）
- `.github/workflows/line-oauth-binding.yml` — LINE OAuth 綁定 GitHub Actions 工作流
- `.github/workflows/line-webhook-receiver.yml` — LINE Webhook 接收工作流
- `.github/workflows/send-loan-notifications.yml` — 借款通知工作流
