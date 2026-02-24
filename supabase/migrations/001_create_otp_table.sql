-- supabase/migrations/001_create_otp_table.sql
-- 創建 otp_codes 表，用於儲存 Email OTP 驗證碼

-- ============================================================
-- 建立 otp_codes 資料表
-- ============================================================
CREATE TABLE IF NOT EXISTS public.otp_codes (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  email        TEXT        NOT NULL,
  code         TEXT        NOT NULL,
  verified     BOOLEAN     NOT NULL DEFAULT false,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at   TIMESTAMPTZ NOT NULL,
  verified_at  TIMESTAMPTZ,
  attempts     INT         NOT NULL DEFAULT 0,
  max_attempts INT         NOT NULL DEFAULT 5
);

-- ============================================================
-- 建立索引，加速查詢
-- ============================================================

-- 複合索引：覆蓋 verify-otp 的主要查詢模式（email + verified + expires_at）
CREATE INDEX IF NOT EXISTS idx_otp_codes_email_verified_expires
  ON public.otp_codes (email, verified, expires_at);

-- 依過期時間查詢，方便清理過期資料
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires_at
  ON public.otp_codes (expires_at);

-- ============================================================
-- 建立自動清理過期 OTP 的函式與觸發器
-- ============================================================

-- 清理函式：刪除 expires_at 早於現在的所有記錄
CREATE OR REPLACE FUNCTION public.cleanup_expired_otp_codes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  DELETE FROM public.otp_codes
  WHERE expires_at < now();
  RETURN NEW;
END;
$$;

-- 觸發器：每次插入新記錄時，自動執行清理
CREATE OR REPLACE TRIGGER trg_cleanup_expired_otp_codes
  AFTER INSERT ON public.otp_codes
  EXECUTE FUNCTION public.cleanup_expired_otp_codes();
