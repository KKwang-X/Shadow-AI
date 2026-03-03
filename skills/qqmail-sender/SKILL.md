---
name: qqmail-sender
description: QQ邮箱发送工具。通过QQ邮箱SMTP发送邮件通知。Use when: (1) 需要发送邮件通知, (2) 需要QQ邮箱发送功能, (3) 系统告警/日报等邮件发送。
---

# QQ Mail Sender

QQ邮箱发送工具，支持通过SMTP发送邮件。

## 配置

在 `config.json` 中配置：
```json
{
  "email": "your-qq@qq.com",
  "auth_code": "your-auth-code"
}
```

或使用环境变量：
```bash
export QQMAIL_EMAIL="your-qq@qq.com"
export QQMAIL_AUTH_CODE="your-auth-code"
```

## 使用方法

### 命令行
```bash
python3 qqmail.py send "recipient@example.com" "邮件主题" "邮件正文"
```

### 在代码中使用
```python
from qqmail import send_email

send_email(
    to_email="recipient@example.com",
    subject="测试邮件",
    body="这是邮件内容"
)
```

## 获取QQ邮箱授权码

1. 登录QQ邮箱网页版
2. 设置 → 账户 → 开启SMTP服务
3. 生成授权码（不是邮箱密码）

## 注意事项

- 使用授权码，不是邮箱密码
- 确保QQ邮箱已开启SMTP服务
- 每日发送有限额（通常几百封）
