# Email OTP 驗證系統設置指南

本文件說明如何部署並使用基於 **SendGrid** 和 **Supabase Edge Functions** 的 Email OTP 驗證系統。

---

## 目錄

1. [系統架構](#系統架構)
2. [前置需求](#前置需求)
3. [設定 SendGrid API Key](#設定-sendgrid-api-key)
4. [執行 SQL 遷移](#執行-sql-遷移)
5. [部署 Edge Functions](#部署-edge-functions)
6. [API 端點說明](#api-端點說明)
7. [郵件格式](#郵件格式)

---

## 系統架構

```
用戶端
  │
  ├─ POST /functions/v1/send-otp   ──► send-otp Edge Function
  │                                        │
  │                                        ├─ 生成 6 位 OTP
  │                                        ├─ 寫入 otp_codes 表
  │                                        └─ 透過 SendGrid 發送郵件
  │
  └─ POST /functions/v1/verify-otp ──► verify-otp Edge Function
                                           │
                                           ├─ 查詢 otp_codes 表
                                           ├─ 驗證碼比對
                                           └─ 標記為已驗證
```

---

## 前置需求

- [Supabase](https://supabase.com/) 專案（已建立）
- [SendGrid](https://sendgrid.com/) 帳號，並完成寄件網域驗證（`axnihao.com`）
- [Supabase CLI](https://supabase.com/docs/guides/cli) 已安裝

---

## 設定 SendGrid API Key

1. 登入 [SendGrid 後台](https://app.sendgrid.com/)，前往 **Settings → API Keys**。
2. 建立一個新的 API Key，選擇 **Mail Send** 權限（Full Access）。
3. 複製產生的 API Key。

### 將 API Key 設定為 Supabase Secret

```bash
supabase secrets set SENDGRID_API_KEY=your_sendgrid_api_key_here
```

驗證已設定成功：

```bash
supabase secrets list
```

---

## 執行 SQL 遷移

### 方法一：使用 Supabase CLI（推薦）

```bash
supabase db push
```

### 方法二：手動執行

1. 前往 **Supabase Dashboard → SQL Editor**。
2. 複製 `supabase/migrations/001_create_otp_table.sql` 的內容並執行。

執行後，資料庫將新增 `otp_codes` 表及相關索引和觸發器。

---

## 部署 Edge Functions

### 部署 send-otp

```bash
supabase functions deploy send-otp
```

### 部署 verify-otp

```bash
supabase functions deploy verify-otp
```

### 一次部署全部

```bash
supabase functions deploy
```

---

## API 端點說明

### POST `/functions/v1/send-otp`

發送 OTP 驗證碼到指定信箱。

**請求 Headers**

```
Content-Type: application/json
Authorization: Bearer <SUPABASE_ANON_KEY>
```

**請求 Body**

```json
{
  "email": "user@example.com"
}
```

**成功回應（HTTP 200）**

```json
{
  "message": "OTP sent successfully"
}
```

**錯誤回應**

| HTTP 狀態碼 | 說明 |
|-------------|------|
| 400 | 缺少或格式不正確的 email |
| 405 | 非 POST 請求 |
| 500 | 伺服器設定錯誤或資料庫錯誤 |
| 502 | SendGrid 發送郵件失敗 |

---

### POST `/functions/v1/verify-otp`

驗證使用者輸入的 OTP 碼。

**請求 Headers**

```
Content-Type: application/json
Authorization: Bearer <SUPABASE_ANON_KEY>
```

**請求 Body**

```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**成功回應（HTTP 200）**

```json
{
  "message": "OTP verified successfully",
  "email": "user@example.com"
}
```

**錯誤回應**

| HTTP 狀態碼 | 說明 |
|-------------|------|
| 400 | 缺少 email 或 code 欄位 |
| 401 | 驗證碼錯誤、已過期或嘗試次數超過上限（5 次） |
| 405 | 非 POST 請求 |
| 500 | 伺服器設定錯誤或資料庫錯誤 |

---

## 郵件格式

- **寄件人**：`noreply@axnihao.com`（安心借貸網）
- **主旨**：`🔐 安心借貸網驗證碼 - 10 分鐘內有效`
- **格式**：HTML 郵件

郵件內容包含：

1. 品牌標題
2. 6 位數字驗證碼（大字體顯示）
3. 有效時間提示（10 分鐘）
4. 安全提示事項

---

## otp_codes 資料表結構

| 欄位 | 型態 | 說明 |
|------|------|------|
| `id` | UUID | 主鍵，自動生成 |
| `email` | TEXT | 收件人信箱 |
| `code` | TEXT | 6 位驗證碼 |
| `verified` | BOOLEAN | 是否已驗證（預設 `false`） |
| `created_at` | TIMESTAMPTZ | 建立時間 |
| `expires_at` | TIMESTAMPTZ | 過期時間（建立後 10 分鐘） |
| `verified_at` | TIMESTAMPTZ | 驗證成功時間 |
| `attempts` | INT | 已嘗試次數（預設 `0`） |
| `max_attempts` | INT | 最大允許嘗試次數（預設 `5`） |
