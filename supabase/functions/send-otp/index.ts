// supabase/functions/send-otp/index.ts
// Supabase Edge Function: 生成並通過 SendGrid 發送 Email OTP 驗證碼

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send";
const OTP_EXPIRY_MINUTES = 10;

/** 生成 6 位數字驗證碼（使用 crypto.getRandomValues 確保加密安全性） */
function generateOtp(): string {
  const buf = new Uint32Array(1);
  crypto.getRandomValues(buf);
  // 取 0–999999 的範圍，補零至 6 位
  const n = buf[0] % 1_000_000;
  return n.toString().padStart(6, "0");
}

/** 建立 OTP 郵件的 HTML 內容 */
function buildEmailHtml(otp: string): string {
  return `
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <title>安心借貸網驗證碼</title>
</head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <tr>
            <td align="center" style="padding-bottom:24px;">
              <h1 style="color:#1a73e8;font-size:24px;margin:0;">🔐 安心借貸網</h1>
            </td>
          </tr>
          <tr>
            <td style="font-size:16px;color:#333;padding-bottom:16px;">
              您好，<br/><br/>
              您的電子郵件驗證碼如下，請在 <strong>${OTP_EXPIRY_MINUTES} 分鐘</strong>內使用：
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:24px 0;">
              <span style="display:inline-block;letter-spacing:8px;font-size:36px;
                           font-weight:bold;color:#1a73e8;background:#eaf2ff;
                           padding:16px 32px;border-radius:8px;">
                ${otp}
              </span>
            </td>
          </tr>
          <tr>
            <td style="font-size:14px;color:#666;padding-top:16px;border-top:1px solid #eee;">
              ⚠️ 安全提示：
              <ul style="margin:8px 0;padding-left:20px;">
                <li>請勿將此驗證碼分享給任何人，包括客服人員。</li>
                <li>驗證碼將於 ${OTP_EXPIRY_MINUTES} 分鐘後自動失效。</li>
                <li>若非您本人操作，請忽略此郵件。</li>
              </ul>
            </td>
          </tr>
          <tr>
            <td style="font-size:12px;color:#aaa;padding-top:24px;text-align:center;">
              © 安心借貸網 | 此郵件由系統自動發送，請勿直接回覆。
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
  `.trim();
}

serve(async (req: Request) => {
  // 僅接受 POST 請求
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  let email: string;
  try {
    const body = await req.json();
    email = (body?.email ?? "").trim().toLowerCase();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // 基本 email 格式驗證
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return new Response(JSON.stringify({ error: "Invalid email address" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // 讀取環境變數
  const sendgridApiKey = Deno.env.get("SENDGRID_API_KEY");
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!sendgridApiKey || !supabaseUrl || !supabaseServiceKey) {
    console.error("Missing required environment variables");
    return new Response(
      JSON.stringify({ error: "Server configuration error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // 初始化 Supabase 客戶端（使用 service role key，繞過 RLS）
  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  // 生成驗證碼與過期時間
  const otp = generateOtp();
  const expiresAt = new Date(Date.now() + OTP_EXPIRY_MINUTES * 60 * 1000).toISOString();

  // 將 OTP 儲存至資料庫
  const { error: dbError } = await supabase.from("otp_codes").insert({
    email,
    code: otp,
    expires_at: expiresAt,
  });

  if (dbError) {
    console.error("DB insert error:", dbError.message);
    return new Response(
      JSON.stringify({ error: "Failed to store OTP" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // 透過 SendGrid REST API 發送郵件
  const mailPayload = {
    personalizations: [{ to: [{ email }] }],
    from: { email: "noreply@axnihao.com", name: "安心借貸網" },
    subject: "🔐 安心借貸網驗證碼 - 10 分鐘內有效",
    content: [{ type: "text/html", value: buildEmailHtml(otp) }],
  };

  const sgResponse = await fetch(SENDGRID_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${sendgridApiKey}`,
    },
    body: JSON.stringify(mailPayload),
  });

  if (!sgResponse.ok) {
    const sgBody = await sgResponse.text();
    console.error("SendGrid error:", sgResponse.status, sgBody);
    return new Response(
      JSON.stringify({ error: "Failed to send email" }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }

  return new Response(
    JSON.stringify({ message: "OTP sent successfully" }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
});
