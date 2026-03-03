---
name: qqmail-sender
description: QQ邮箱发送工具 - 国内OpenClaw用户最便捷的邮件方案。通过QQ邮箱SMTP发送邮件，无需海外邮箱。Use when: (1) 需要发送邮件通知, (2) 国内网络环境下的邮件发送, (3) 系统告警/日报等自动化邮件。
---

# QQ Mail Sender - QQ邮箱发送工具

> 🇨🇳 **国内 OpenClaw 用户最便捷的邮件方案**
> 
> 无需 Gmail/Outlook，直接使用 QQ 邮箱，国内网络畅通无阻。

---

## 为什么选择 QQ 邮箱？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Gmail** | 国际通用 | 国内访问困难，需要翻墙 |
| **Outlook** | 微软生态 | 国内偶发连接问题 |
| **QQ邮箱** ✅ | 国内畅通，人人有号 | 新号需等待 14 天才能开 SMTP |

**结论：** 对于国内 OpenClaw 部署，QQ 邮箱是最稳定、最便捷的选择。

---

## 完整配置流程（从0到1）

### 第一步：准备 QQ 邮箱

1. **注册/登录 QQ 邮箱**
   - 访问 https://mail.qq.com
   - 使用 QQ 号登录（如果没有，先注册 QQ）

2. **⚠️ 重要：新号等待期**
   - 新注册的 QQ 号需要等待 **14 天** 才能开启 SMTP
   - 老号可以直接使用

### 第二步：开启 SMTP 服务

1. 登录 QQ 邮箱网页版
2. 点击顶部 **「设置」** → **「账户」**
3. 找到 **「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」**
4. 开启 **「SMTP服务」**
   - 需要发送短信验证
   - 验证后会显示 **授权码**（16位字符串）

   ![开启SMTP](https://res.wx.qq.com/a/fed_upload/6ba2c3d9-1a5e-4c9e-9b3e-8e5f4a6c2d1b.png)

### 第三步：保存授权码

- 授权码只显示一次，务必保存
- 格式类似：`kveortouoijibhff`
- ⚠️ **这不是你的 QQ 密码！**

### 第四步：配置 OpenClaw

**方式1：配置文件（推荐）**

创建 `skills/qqmail-sender/config.json`：
```json
{
  "email": "你的QQ号@qq.com",
  "auth_code": "你的授权码"
}
```

**方式2：环境变量**

```bash
export QQMAIL_EMAIL="你的QQ号@qq.com"
export QQMAIL_AUTH_CODE="你的授权码"
```

添加到 `~/.bashrc` 使其永久生效：
```bash
echo 'export QQMAIL_EMAIL="你的QQ号@qq.com"' >> ~/.bashrc
echo 'export QQMAIL_AUTH_CODE="你的授权码"' >> ~/.bashrc
source ~/.bashrc
```

---

## 使用方法

### 命令行发送

```bash
# 基础用法
python3 skills/qqmail-sender/qqmail.py "收件人@example.com" "邮件主题" "邮件正文"

# 示例：发送测试邮件
python3 skills/qqmail-sender/qqmail.py "465948398@qq.com" "系统通知" "OpenClaw 服务运行正常"
```

### Python 代码调用

```python
import sys
sys.path.insert(0, 'skills/qqmail-sender')
from qqmail import send_email

# 发送邮件
send_email(
    to_email="收件人@example.com",
    subject="系统告警",
    body="CPU使用率超过90%"
)
```

### 在 Skill 中使用

```python
# 在其他 skill 中调用
import subprocess

def notify_admin(message):
    subprocess.run([
        "python3", "skills/qqmail-sender/qqmail.py",
        "admin@example.com",
        "系统通知",
        message
    ])
```

---

## 典型使用场景

### 1. 系统监控告警

```bash
# 在 cron 任务中使用
*/30 * * * * python3 check_system.py || python3 skills/qqmail-sender/qqmail.py "admin@qq.com" "服务器告警" "服务异常"
```

### 2. 每日日报

```python
# 在 skill 中集成
def send_daily_report():
    report = generate_report()
    send_email(
        to_email="manager@company.com",
        subject=f"日报 {datetime.now().strftime('%Y-%m-%d')}",
        body=report
    )
```

### 3. AI 任务完成通知

```python
# 长任务完成后发送通知
def on_task_complete(task_name, result):
    send_email(
        to_email="user@qq.com",
        subject=f"任务完成: {task_name}",
        body=f"任务已完成，结果:\n{result}"
    )
```

---

## 常见问题

### Q: 新 QQ 号无法获取授权码？
A: 新注册的 QQ 号需要等待 **14 天** 才能开启 SMTP 服务。建议：
- 使用老 QQ 号
- 或先注册，14 天后再配置

### Q: 提示 "授权码错误"？
A: 注意区分：
- ❌ QQ 登录密码
- ✅ SMTP 授权码（16位，开启服务时生成）

### Q: 发送失败，连接超时？
A: 检查：
1. 服务器是否能访问 `smtp.qq.com:587`
2. 防火墙是否放行 587 端口
3. 阿里云安全组是否放行出站 587

### Q: 每天能发多少封？
A: QQ 邮箱限制：
- 普通用户：约 100-200 封/天
- 会员用户：约 500 封/天
- 超出限制会临时封禁 SMTP 功能

---

## 技术细节

| 项目 | 值 |
|------|-----|
| SMTP 服务器 | `smtp.qq.com` |
| 端口 | `587` (TLS) |
| 认证方式 | 授权码（非密码） |
| 加密 | STARTTLS |

---

## 与其他方案对比

| 特性 | QQ邮箱 | Gmail | 阿里云邮件推送 |
|------|--------|-------|---------------|
| 国内访问 | ✅ 畅通 | ❌ 需翻墙 | ✅ 畅通 |
| 免费额度 | ✅ 充足 | ✅ 充足 | ⚠️ 需申请 |
| 配置难度 | ✅ 简单 | 中等 | 复杂 |
| 企业场景 | ⚠️ 个人为主 | ✅ 支持 | ✅ 专业 |

**推荐：**
- 个人/小团队：QQ 邮箱（本方案）
- 企业场景：阿里云邮件推送 + 企业邮箱

---

## 安全提示

1. **授权码保管**
   - 不要上传到公开仓库
   - 使用 `.gitignore` 忽略 `config.json`
   - 优先使用环境变量

2. **config.json 模板**
   ```json
   {
     "email": "YOUR_QQ@qq.com",
     "auth_code": "YOUR_AUTH_CODE"
   }
   ```

3. **生产环境建议**
   ```bash
   # 使用环境变量，不写入文件
   export QQMAIL_EMAIL="${QQMAIL_EMAIL}"
   export QQMAIL_AUTH_CODE="${QQMAIL_AUTH_CODE}"
   ```

---

## 开源协议

MIT License - 详见 [LICENSE](../../LICENSE)

---

<p align="center">
  为 🇨🇳 国内 OpenClaw 用户打造
</p>
