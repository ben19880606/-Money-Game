// supabase/functions/verify-otp/index.ts
// Supabase Edge Function: 驗證使用者提交的 Email OTP 驗證碼

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const MAX_ATTEMPTS = 5;

serve(async (req: Request) => {
  // 僅接受 POST 請求
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  let email: string;
  let code: string;
  try {
    const body = await req.json();
    email = (body?.email ?? "").trim().toLowerCase();
    code = (body?.code ?? "").trim();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // 基本輸入驗證
  if (!email || !code) {
    return new Response(
      JSON.stringify({ error: "email and code are required" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  // 讀取環境變數
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!supabaseUrl || !supabaseServiceKey) {
    console.error("Missing required environment variables");
    return new Response(
      JSON.stringify({ error: "Server configuration error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // 初始化 Supabase 客戶端（使用 service role key，繞過 RLS）
  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  // 查詢最新一筆符合 email 的未驗證且未過期的 OTP 記錄
  const now = new Date().toISOString();
  const { data: records, error: queryError } = await supabase
    .from("otp_codes")
    .select("id, code, attempts, max_attempts, expires_at, verified")
    .eq("email", email)
    .eq("verified", false)
    .gt("expires_at", now)
    .order("created_at", { ascending: false })
    .limit(1);

  if (queryError) {
    console.error("DB query error:", queryError.message);
    return new Response(
      JSON.stringify({ error: "Database error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // 找不到有效記錄（驗證碼不存在或已過期）
  if (!records || records.length === 0) {
    return new Response(
      JSON.stringify({ error: "OTP not found or expired" }),
      { status: 401, headers: { "Content-Type": "application/json" } }
    );
  }

  const record = records[0];
  const maxAttempts: number = record.max_attempts ?? MAX_ATTEMPTS;

  // 檢查嘗試次數是否已超過上限
  if (record.attempts >= maxAttempts) {
    return new Response(
      JSON.stringify({ error: "Maximum verification attempts exceeded" }),
      { status: 401, headers: { "Content-Type": "application/json" } }
    );
  }

  // 先遞增嘗試次數（無論驗證是否成功，防止暴力破解）
  const { error: updateAttemptsError } = await supabase
    .from("otp_codes")
    .update({ attempts: record.attempts + 1 })
    .eq("id", record.id);

  if (updateAttemptsError) {
    console.error("Failed to update attempts:", updateAttemptsError.message);
    // 非致命錯誤，繼續驗證流程
  }

  // 比對驗證碼
  if (record.code !== code) {
    return new Response(
      JSON.stringify({ error: "Invalid OTP code" }),
      { status: 401, headers: { "Content-Type": "application/json" } }
    );
  }

  // 驗證成功：標記為已驗證並記錄驗證時間
  const verifiedAt = new Date().toISOString();
  const { error: verifyError } = await supabase
    .from("otp_codes")
    .update({ verified: true, verified_at: verifiedAt })
    .eq("id", record.id);

  if (verifyError) {
    console.error("Failed to mark OTP as verified:", verifyError.message);
    return new Response(
      JSON.stringify({ error: "Failed to complete verification" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  return new Response(
    JSON.stringify({ message: "OTP verified successfully", email }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
});
