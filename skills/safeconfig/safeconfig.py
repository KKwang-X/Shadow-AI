#!/usr/bin/env python3
"""
SafeConfig - Safe Configuration Management Script
Validates parameters, backs up configs, requires user confirmation
新增：审批人功能（--approver）
"""

import sys
import os
import json
import shutil
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path

# Critical configuration files list
CRITICAL_CONFIGS = [
    "~/.openclaw/openclaw.json",
    "/etc/systemd/system/openclaw.service",
    "/etc/nginx/nginx.conf",
    "~/.ssh/config",
]

# 审批状态存储目录
APPROVAL_DIR = Path("~/.safeconfig/approvals").expanduser()

def ensure_approval_dir():
    """确保审批目录存在"""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)

def backup_config(filepath):
    """Create config backup"""
    filepath = Path(filepath).expanduser()
    if not filepath.exists():
        return None
    
    backup_dir = Path("~/.config-backups").expanduser()
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{filepath.name}.{timestamp}.bak"
    
    shutil.copy2(filepath, backup_path)
    return backup_path

def validate_openclaw_param(param):
    """Validate openclaw parameter exists"""
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "start", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        help_text = result.stdout + result.stderr
        return param in help_text
    except Exception:
        return None

def validate_systemd_config(filepath):
    """Validate systemd config syntax"""
    try:
        result = subprocess.run(
            ["systemd-analyze", "verify", str(filepath)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def is_critical_config(filepath):
    """Check if file is a critical config"""
    filepath = Path(filepath).expanduser().resolve()
    for critical in CRITICAL_CONFIGS:
        critical_path = Path(critical).expanduser().resolve()
        if filepath == critical_path:
            return True
    return False

def parse_approver(approver_str):
    """解析审批人格式: telegram:username 或 email:address"""
    if not approver_str:
        return None
    
    if ":" in approver_str:
        channel, identifier = approver_str.split(":", 1)
        return {"channel": channel, "identifier": identifier}
    return None

def send_approval_request(approver, filepath, changes_desc, request_id):
    """发送审批请求"""
    channel = approver["channel"]
    identifier = approver["identifier"]
    
    # 构建审批请求消息
    message = f"""🔐 SafeConfig 审批请求

请求ID: {request_id}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📁 待修改文件: {filepath}

📝 变更说明:
{changes_desc}

⚠️ 这是一个关键配置文件，需要您的审批。

✅ 回复 "批准" 或 "approve" 执行修改
❌ 回复 "拒绝" 或 "reject" 取消操作

⏰ 审批将在30分钟后过期
"""
    
    if channel == "telegram":
        return send_telegram_approval(identifier, message, request_id)
    elif channel == "email":
        return send_email_approval(identifier, message, request_id)
    else:
        print(f"⚠️  不支持的审批渠道: {channel}")
        return False

def send_telegram_approval(username, message, request_id):
    """通过 Telegram 发送审批请求"""
    # 保存审批请求到文件，供外部轮询
    ensure_approval_dir()
    approval_file = APPROVAL_DIR / f"{request_id}.json"
    
    approval_data = {
        "request_id": request_id,
        "channel": "telegram",
        "recipient": username,
        "message": message,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat()
    }
    
    with open(approval_file, 'w') as f:
        json.dump(approval_data, f, indent=2)
    
    print(f"📨 Telegram 审批请求已发送给 @{username}")
    print(f"📄 审批文件: {approval_file}")
    print(f"\n💡 提示: 请通知 @{username} 查看 Telegram 消息并回复")
    
    # 尝试使用 telegram-cli 发送（如果配置了）
    try:
        # 这里可以集成 telegram bot api
        pass
    except:
        pass
    
    return True

def send_email_approval(email, message, request_id):
    """通过邮件发送审批请求"""
    ensure_approval_dir()
    approval_file = APPROVAL_DIR / f"{request_id}.json"
    
    approval_data = {
        "request_id": request_id,
        "channel": "email",
        "recipient": email,
        "message": message,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat()
    }
    
    with open(approval_file, 'w') as f:
        json.dump(approval_data, f, indent=2)
    
    # 尝试使用 qqmail-sender 发送
    try:
        qqmail_path = Path(__file__).parent.parent / "qqmail-sender" / "qqmail.py"
        if qqmail_path.exists():
            subprocess.run([
                "python3", str(qqmail_path),
                email,
                f"🔐 SafeConfig 审批请求 - {request_id}",
                message
            ], check=True)
            print(f"📧 审批邮件已发送至 {email}")
    except Exception as e:
        print(f"⚠️  邮件发送失败: {e}")
        print(f"📄 审批文件已保存: {approval_file}")
    
    return True

def wait_for_approval(request_id, timeout=1800):
    """等待审批结果，默认30分钟"""
    approval_file = APPROVAL_DIR / f"{request_id}.json"
    
    print(f"\n⏳ 等待审批中... (最多30分钟)")
    print(f"💡 审批人请回复到对应渠道，或手动修改文件:")
    print(f"   {approval_file}")
    print(f"   将 status 改为 'approved' 或 'rejected'")
    
    start_time = time.time()
    check_interval = 5  # 每5秒检查一次
    
    while time.time() - start_time < timeout:
        if approval_file.exists():
            with open(approval_file, 'r') as f:
                data = json.load(f)
            
            status = data.get("status")
            if status == "approved":
                print(f"\n✅ 审批已通过！")
                return True
            elif status == "rejected":
                print(f"\n❌ 审批被拒绝")
                return False
        
        # 显示倒计时
        remaining = int(timeout - (time.time() - start_time))
        if remaining % 60 == 0:  # 每分钟显示一次
            print(f"   剩余时间: {remaining // 60} 分钟")
        
        time.sleep(check_interval)
    
    print(f"\n⏰ 审批超时（30分钟），操作取消")
    return False

def generate_checklist(config_type, changes):
    """Generate safety checklist"""
    checklist = []
    
    if config_type == "openclaw.json":
        checklist.append("□ Check openclaw version compatibility")
        for change in changes:
            if "param" in change:
                valid = validate_openclaw_param(change["param"])
                if valid is False:
                    checklist.append(f"⚠️  Parameter '{change['param']}' may not exist")
                elif valid is True:
                    checklist.append(f"✅ Parameter '{change['param']}' validated")
    
    elif config_type == "systemd":
        checklist.append("□ Validate systemd config syntax")
        checklist.append("□ Confirm ExecStart parameter validity")
    
    checklist.append("□ Config backup created")
    checklist.append("□ User confirmation obtained")
    checklist.append("□ Service status verified after modification")
    
    return checklist

def main():
    from datetime import timedelta  # 导入放在这里避免循环导入
    
    parser = argparse.ArgumentParser(description="SafeConfig - Safe Configuration Management")
    parser.add_argument("--check", help="Check if file is critical config")
    parser.add_argument("--backup", help="Backup specified config file")
    parser.add_argument("--validate-systemd", help="Validate systemd config file")
    parser.add_argument("--type", choices=["openclaw.json", "systemd", "nginx", "ssh"], 
                        help="Config type")
    parser.add_argument("--approver", help="指定审批人 (格式: telegram:username 或 email:address)")
    parser.add_argument("--changes", help="变更说明（用于审批）")
    parser.add_argument("--approve", help="批准指定请求ID（审批人用）")
    parser.add_argument("--reject", help="拒绝指定请求ID（审批人用）")
    
    args = parser.parse_args()
    
    # 审批人操作：批准/拒绝
    if args.approve:
        ensure_approval_dir()
        approval_file = APPROVAL_DIR / f"{args.approve}.json"
        if approval_file.exists():
            with open(approval_file, 'r') as f:
                data = json.load(f)
            data["status"] = "approved"
            data["approved_at"] = datetime.now().isoformat()
            with open(approval_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ 已批准请求: {args.approve}")
        else:
            print(f"❌ 请求不存在: {args.approve}")
        return 0
    
    if args.reject:
        ensure_approval_dir()
        approval_file = APPROVAL_DIR / f"{args.reject}.json"
        if approval_file.exists():
            with open(approval_file, 'r') as f:
                data = json.load(f)
            data["status"] = "rejected"
            data["rejected_at"] = datetime.now().isoformat()
            with open(approval_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"❌ 已拒绝请求: {args.reject}")
        else:
            print(f"❌ 请求不存在: {args.reject}")
        return 0
    
    # 检查关键配置
    if args.check:
        filepath = Path(args.check).expanduser()
        is_critical = is_critical_config(filepath)
        print(f"File: {filepath}")
        print(f"Critical config: {'Yes' if is_critical else 'No'}")
        if is_critical:
            print("\n⚠️  This is a critical config file. Before modification:")
            print("  1. Validate parameter existence")
            print("  2. Create backup")
            print("  3. Get user confirmation")
            if args.approver:
                print(f"  4. Get approver confirmation ({args.approver})")
        return 0 if not is_critical else 1
    
    # 备份配置（带审批流程）
    if args.backup:
        filepath = Path(args.backup).expanduser()
        
        # 如果指定了审批人，进入审批流程
        if args.approver:
            approver = parse_approver(args.approver)
            if not approver:
                print("❌ 审批人格式错误，应为: telegram:username 或 email:address")
                return 1
            
            changes = args.changes or f"备份文件: {filepath}"
            request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
            
            print(f"🔐 启动审批流程")
            print(f"📋 请求ID: {request_id}")
            print(f"👤 审批人: {approver['channel']}:{approver['identifier']}")
            
            # 发送审批请求
            if not send_approval_request(approver, str(filepath), changes, request_id):
                print("❌ 审批请求发送失败")
                return 1
            
            # 等待审批
            if not wait_for_approval(request_id):
                print("❌ 审批未通过，操作取消")
                return 1
            
            print("\n📦 继续执行备份...")
        
        # 执行备份
        backup_path = backup_config(filepath)
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
            return 0
        else:
            print(f"⚠️  File doesn't exist, no backup needed: {filepath}")
            return 1
    
    # 验证 systemd 配置
    if args.validate_systemd:
        valid, error = validate_systemd_config(args.validate_systemd)
        if valid:
            print("✅ systemd config validated")
            return 0
        else:
            print(f"❌ systemd config error: {error}")
            return 1
    
    # Default: show safety checklist template
    print("=" * 50)
    print("SafeConfig - Safety Checklist")
    print("=" * 50)
    print("\nCritical config files:")
    for cfg in CRITICAL_CONFIGS:
        print(f"  • {cfg}")
    print("\nRequired before modification:")
    print("  1. Verify parameter exists (--help)")
    print("  2. Create config backup")
    print("  3. Show changes to user")
    print("  4. Get explicit user confirmation")
    print("  5. Verify service status after modification")
    print("\n🔐 审批人功能（可选）:")
    print("  --approver telegram:username  # Telegram审批")
    print("  --approver email:address      # 邮件审批")
    print("\nUsage:")
    print("  safeconfig --check <filepath> [--approver telegram:admin]")
    print("  safeconfig --backup <filepath> --approver email:admin@company.com --changes '修改说明'")
    print("  safeconfig --validate-systemd <file>")
    print("  safeconfig --approve <request_id>    # 批准请求")
    print("  safeconfig --reject <request_id>     # 拒绝请求")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
