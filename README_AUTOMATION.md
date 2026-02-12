# Money-Game AI 工作流自动化系统

## 📋 系统概述

这是为 Money-Game 借贷媒介平台搭建的完整自动化工作流系统，包括：

- ✅ **支付自动激活** - 自动验证金主支付并激活会员资格
- ✅ **周报告生成** - 每周一自动生成会员统计报告
- ✅ **安全监控** - 实时监控网站安全状态并告警

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────┐
│         Readdy AI 网站 (axnihao.com)        │
├─────────────────────────────────────────────┤
│    前端会员支付 → 填写汇款后五码 + 照片    │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│       Supabase 数据库 (profiles 表)         │
│  ├─ id (用户ID)                            │
│  ├─ email (邮箱)                           │
│  ├─ membership_type (borrower/lender)      │
│  ├─ payment_verified (YES/NO)              │
│  ├─ payment_last_five_digits (汇款后五码)  │
│  ├─ membership_tier (flagship/prestige...) │
│  ├─ activated_at (激活时间)                │
│  └─ created_at (创建时间)                  │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│     GitHub Actions 自动化工作流            │
├─────────────────────────────────────────────┤
│                                             │
│  1️⃣ payment-auto-activation.yml             │
│     运行频率: 每小时执行一次               │
│     功能: 自动激活已支付的金主会员          │
│                                             │
│  2️⃣ weekly-member-report.yml                │
│     运行频率: 每周一早上 8 点              │
│     功能: 生成周会员统计报告               │
│                                             │
│  3️⃣ security-monitor.yml                    │
│     运行频率: 每 6 小时检查一次            │
│     功能: 监控网站安全状况                 │
│                                             │
└──────────────┬──────────────────────────────┘
               │
               ↓
        📧 告警邮件
    aijinetwork@gmail.com
```

---

## 📦 文件结构

```
Money-Game/
├── .github/
│   └── workflows/
│       ├── payment-auto-activation.yml    # 支付激活工作流
│       ├── weekly-member-report.yml       # 周报告工作流
│       └── security-monitor.yml           # 安全监控工作流
├── scripts/
│   ├── supabase_client.py                # Supabase 连接库
│   ├── payment_verifier.py               # 支付验证脚本
│   ├── member_reporter.py                # 报告生成脚本
│   └── security_checker.py               # 安全检查脚本
├── requirements.txt                      # Python 依赖
└── README_AUTOMATION.md                  # 本文档
```

---

## 🔐 GitHub Secrets 配置

> ⚠️ 重要：这些密钥应该在 GitHub 仓库中安全存储

在你的 GitHub 仓库中，进入 **Settings → Secrets and variables → Actions**，添加以下 Secrets：

| Secret 名称 | 说明 | 示例 |
|-----------|------|------|
| `SUPABASE_URL` | Supabase 项目 URL | `https://jyqmpfqpmglwnzselafe.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service_role 密钥 | (从 Supabase 控制面板获取) |
| `SMTP_USERNAME` | Gmail 邮箱地址 | `your-email@gmail.com` |
| `SMTP_PASSWORD` | Gmail 应用密码 | (生成应用专用密码) |

### 如何获取 Gmail 应用密码？

1. 启用 Google 账户的两步验证
2. 进入 https://myaccount.google.com/apppasswords
3. 选择 Mail 和 Windows Computer
4. 生成 16 位应用密码
5. 将该密码保存到 GitHub Secrets 中的 `SMTP_PASSWORD`

---

## 🚀 工作流详解

### 1️⃣ 支付自动激活工作流 (`payment-auto-activation.yml`)

**运行频率：** 每小时执行一次

**处理流程：**
```
1. 查询 Supabase 获取所有未验证支付的金主会员
2. 检查是否有 payment_last_five_digits 字段
3. 如果有 → 判定为已支付
4. 自动更新会员状态：
   ├─ payment_verified = YES
   ├─ activated_at = 当前时间
   └─ membership_tier = 根据支付金额判定 (目前默认 flagship)
5. 发送激活报告邮件
```

**关键字段更新：**
- `payment_verified`: `false` → `true` (YES)
- `activated_at`: `NULL` → `2026-02-12T08:30:00Z` (当前时间)

---

### 2️⃣ 周报告工作流 (`weekly-member-report.yml`)

**运行频率：** 每周一早上 8 点（UTC）

**报告内容：**
```
【本周新加入会员】
├─ 借款人(Borrower): XX 位
└─ 金主(Lender): XX 位

【金主会员激活情况】
├─ 已激活金主: XX 位
├─ 待激活金主: XX 位
└─ 激活率: XX%

【平台整体数据】
├─ 平台总会员数: XX 位
└─ 报告周期: 周一 00:00 ~ 周日 23:59 (UTC)

【系统状态】
└─ ✅ 系统运行正常
```

**数据统计逻辑：**
- 本周新借款人 = `created_at` >= 周一 AND `membership_type` = borrower
- 本周新金主 = `created_at` >= 周一 AND `membership_type` = lender
- 已激活金主 = `activated_at` >= 周一 AND `payment_verified` = true AND `membership_type` = lender
- 待激活金主 = `payment_verified` = false AND `payment_last_five_digits` 不为空

---

### 3️⃣ 安全监控工作流 (`security-monitor.yml`)

**运行频率：** 每 6 小时检查一次

**监控项目：**
```
[1] 网站可用性检查
    ├─ HTTP 状态码 (需要 200)
    └─ 连接超时检测

[2] SSL 证书检查
    ├─ 证书有效期
    └─ 证书完整性

[3] 异常内容检查
    ├─ SQL 错误关键词
    ├─ PHP 错误信息
    ├─ 数据库连接失败
    └─ 其他可疑内容
```

**告警条件：**
- ❌ 网站无法访问 (HTTP 5xx / 连接失败)
- ❌ SSL 证书过期或无效
- ❌ 检测到 SQL 注入迹象
- ❌ 检测到其他攻击迹象

**告警方式：** 邮件发送到 `aijinetwork@gmail.com`

---

## 🛠️ 本地测试

### 前置要求
- Python 3.10+
- pip

### 安装依赖
```bash
pip install -r requirements.txt
```

### 环境配置
创建 `.env` 文件（仅用于本地测试）：
```bash
SUPABASE_URL=https://jyqmpfqpmglwnzselafe.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### 运行脚本

**测试支付验证脚本：**
```bash
python scripts/payment_verifier.py
```

**测试报告生成脚本：**
```bash
python scripts/member_reporter.py
```

**测试安全检查脚本：**
```bash
python scripts/security_checker.py
```

---

## 📊 会员生命周期

### 借款人 (Borrower)
```
注册 → 免费激活 → 立即可用
```

### 金主 (Lender)
```
注册 
  ↓
选择订阅等级（Flagship/Prestige/Platinum）
  ↓
支付订阅费用
  ↓
填入汇款后五码 + 上传凭证
  ↓
财务小编对账 [手动]
  ↓
系统自动激活 [自动]
  ↓
享受会员服务 (30/60/90 天)
```

### 订阅等级说明

| 等级 | 中文 | 时长 | 功能 |
|-----|------|------|------|
| flagship | 旗艦 | 30 天 | 文字广告、私信联络 |
| prestige | 尊榮 | 60 天 | 文字广告、图文广告、私信联络 |
| platinum | 鉑金 | 90 天 | 文字广告、图文广告、私信联络、优先推荐 |

---

## 🔄 工作流触发方式

### 自动触发（定时）
- 所有工作流都会按照设定的时间表自动执行
- 无需手动操作

### 手动触发
在 GitHub 仓库中进入 **Actions** 标签页，可以手动触发任何工作流：
1. 选择工作流
2. 点击 "Run workflow"
3. 选择分支 (main)
4. 点击 "Run workflow"

---

## 📧 邮件配置

所有告警和报告都会发送到 **aijinetwork@gmail.com**

### 邮件类型

| 工作流 | 邮件主题 | 触发条件 |
|-------|--------|--------|
| 支付激活 | `[Money-Game] 金主會員自動激活報告` | 每小时执行 |
| 周报告 | `[Money-Game] 周會員統計報告` | 每周一 8 点 |
| 安全监控 | `⚠️ [Money-Game] 網站安全警告` | 检测到问题 |

---

## 🐛 故障排查

### 问题 1: 工作流未执行
- ✅ 检查 GitHub Actions 是否启用 (Settings → Actions)
- ✅ 检查 Secrets 是否正确配置
- ✅ 检查工作流文件语法是否正确

### 问题 2: 邮件未收到
- ✅ 检查 SMTP_USERNAME 和 SMTP_PASSWORD 是否正确
- ✅ 确认 Gmail 已启用两步验证和应用密码
- ✅ 检查告警邮箱地址是否正确

### 问题 3: Supabase 连接失败
- ✅ 确认 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 正确
- ✅ 检查 Supabase 服务是否在线
- ✅ 查看 GitHub Actions 的详细日志

### 查看工作流日志
1. 进入仓库 → Actions 标签页
2. 选择对应的工作流运行
3. 点击 Job 查看详细日志

---

## 🔒 安全建议

1. **定期轮换 Secrets**
   - 每月轮换一次 Supabase service_role key
   - 每月轮换一次 Gmail 应用密码

2. **监控 Secrets 使用**
   - 定期查看 GitHub Actions 的执行日志
   - 确保只有授权人员可以修改工作流

3. **备份关键数据**
   - 定期备份 Supabase 数据库
   - 保存重要的报告副本

---

## 📞 需要帮助？

如有问题，请检查：
1. 工作流日志 (GitHub Actions)
2. Supabase 数据库日志
3. 邮件垃圾箱（确保邮件未被误判）

---

## 📝 版本历史

- **v1.0** (2026-02-12) - 初始版本
  - 支付自动激活工作流
  - 周报告生成
  - 网站安全监控

---

**最后更新：2026-02-12**
