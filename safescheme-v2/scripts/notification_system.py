#!/usr/bin/env python3
"""
SafeConfig Notification System - 通知系统
支持 Telegram、Email、Webhook 通知
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class NotificationSystem:
    """通知系统"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载通知配置"""
        config_path = Path("~/.safeconfig/notification.json").expanduser()
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            "telegram": {"enabled": False, "chat_id": None},
            "email": {"enabled": False, "address": None},
            "webhook": {"enabled": False, "url": None}
        }
    
    def notify_approval_request(self, request_id: str, changes: str, approver: str):
        """发送审批请求通知"""
        message = f"""🔐 SafeConfig 审批请求

请求ID: {request_id}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 变更说明:
{changes}

⚠️ 需要您的审批

批准命令:
python3 safeconfig-v2.py --approve {request_id}
"""
        
        # Telegram 通知
        if self.config.get("telegram", {}).get("enabled"):
            self._send_telegram(message, approver)
        
        # Email 通知
        if self.config.get("email", {}).get("enabled"):
            self._send_email("SafeConfig 审批请求", message)
        
        # Webhook 通知
        if self.config.get("webhook", {}).get("enabled"):
            self._send_webhook({
                "type": "approval_request",
                "request_id": request_id,
                "changes": changes,
                "timestamp": datetime.now().isoformat()
            })
    
    def notify_completion(self, request_id: str, status: str, changes: str):
        """发送完成通知"""
        icon = "✅" if status == "completed" else "❌" if status == "failed" else "🔄"
        message = f"""{icon} SafeConfig 操作完成

请求ID: {request_id}
状态: {status}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 变更:
{changes}
"""
        
        if self.config.get("telegram", {}).get("enabled"):
            self._send_telegram(message)
    
    def notify_violation(self, violation_type: str, details: str):
        """发送违规告警"""
        message = f"""🚨 SafeConfig 违规告警

类型: {violation_type}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

详情:
{details}

请立即检查！
"""
        
        # 违规告警使用所有渠道
        if self.config.get("telegram", {}).get("enabled"):
            self._send_telegram(message)
        
        if self.config.get("email", {}).get("enabled"):
            self._send_email("🚨 SafeConfig 违规告警", message)
    
    def _send_telegram(self, message: str, chat_id: Optional[str] = None):
        """发送 Telegram 消息"""
        # 使用 qqmail-sender 或其他方式发送
        # 简化实现，实际应该使用 Telegram Bot API
        print(f"[Telegram] {message[:100]}...")
    
    def _send_email(self, subject: str, body: str):
        """发送邮件"""
        email = self.config.get("email", {}).get("address")
        if not email:
            return
        
        # 使用 qqmail-sender
        qqmail_script = Path(__file__).parent / "skills" / "qqmail-sender" / "qqmail.py"
        if qqmail_script.exists():
            subprocess.run([
                "python3", str(qqmail_script),
                email,
                subject,
                body
            ], capture_output=True)
        
        print(f"[Email] To: {email}, Subject: {subject}")
    
    def _send_webhook(self, payload: Dict):
        """发送 Webhook"""
        import urllib.request
        import urllib.error
        
        url = self.config.get("webhook", {}).get("url")
        if not url:
            return
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            urllib.request.urlopen(req, timeout=10)
            print(f"[Webhook] Sent to {url}")
        except Exception as e:
            print(f"[Webhook] Failed: {e}")


def main():
    """测试通知系统"""
    notifier = NotificationSystem()
    
    # 测试审批请求通知
    notifier.notify_approval_request(
        request_id="test-123",
        changes="测试变更",
        approver="telegram:8028839180"
    )
    
    print("\n通知系统测试完成")


if __name__ == "__main__":
    main()
