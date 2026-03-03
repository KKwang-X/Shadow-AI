#!/usr/bin/env python3
"""
QQ Mail Sender - QQ邮箱发送工具
支持通过QQ邮箱SMTP发送邮件
"""

import sys
import os
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# QQ邮箱SMTP配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587  # 使用TLS

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        import json
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def send_email(to_email, subject, body, sender_email=None, auth_code=None):
    """发送邮件"""
    
    # 从参数或配置文件获取
    config = load_config()
    sender = sender_email or config.get('email') or os.getenv('QQMAIL_EMAIL')
    auth = auth_code or config.get('auth_code') or os.getenv('QQMAIL_AUTH_CODE')
    
    if not sender or not auth:
        print("❌ 错误：未配置QQ邮箱")
        print("   请设置环境变量 QQMAIL_EMAIL 和 QQMAIL_AUTH_CODE")
        print("   或创建 config.json 配置文件")
        return False
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 添加正文
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 连接SMTP服务器
        print(f"📧 正在连接 {SMTP_SERVER}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # 启用TLS加密
        
        # 登录
        print(f"🔐 正在登录 {sender}...")
        server.login(sender, auth)
        
        # 发送邮件
        print(f"📤 正在发送邮件到 {to_email}...")
        server.send_message(msg)
        
        # 关闭连接
        server.quit()
        
        print(f"✅ 邮件发送成功！")
        return True
        
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="QQ Mail Sender - QQ邮箱发送工具")
    parser.add_argument("to", help="收件人邮箱地址")
    parser.add_argument("subject", help="邮件主题")
    parser.add_argument("body", help="邮件正文")
    parser.add_argument("--from", dest="sender", help="发件人QQ邮箱（覆盖配置）")
    parser.add_argument("--auth", help="授权码（覆盖配置）")
    
    args = parser.parse_args()
    
    success = send_email(
        to_email=args.to,
        subject=args.subject,
        body=args.body,
        sender_email=args.sender,
        auth_code=args.auth
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
