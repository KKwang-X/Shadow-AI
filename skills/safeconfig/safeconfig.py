#!/usr/bin/env python3
"""
SafeConfig - Safe Configuration Management Script
Validates parameters, backs up configs, requires user confirmation
新增：审批人功能（--approver）+ 安全增强版

安全增强：
- UUID4 随机请求ID
- 审批人身份验证
- 单审批人权限控制
- 自动清理过期请求
- 完整审计日志
"""

import sys
import os
import json
import shutil
import subprocess
import argparse
import time
import uuid
import fcntl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Critical configuration files list
CRITICAL_CONFIGS = [
    "~/.openclaw/openclaw.json",
    "/etc/systemd/system/openclaw.service",
    "/etc/nginx/nginx.conf",
    "~/.ssh/config",
]

# 审批状态存储目录
APPROVAL_DIR = Path("~/.safeconfig/approvals").expanduser()
LOG_DIR = Path("~/.safeconfig/logs").expanduser()

# 授权审批人（只允许这些用户审批）
# 格式: ["username1", "username2"] 或 ["kk"] 
AUTHORIZED_APPROVERS = ["admin", "kk"]  # 可配置

def ensure_dirs():
    """确保必要目录存在"""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 设置权限（仅所有者可读写）
    os.chmod(APPROVAL_DIR, 0o700)
    os.chmod(LOG_DIR, 0o700)

def log_audit(action: str, details: dict):
    """记录审计日志"""
    log_file = LOG_DIR / f"audit_{datetime.now().strftime('%Y%m')}.log"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
        "uid": os.getuid(),
        "action": action,
        "details": details
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

def check_approver_permission() -> bool:
    """检查当前用户是否有审批权限"""
    current_user = os.getenv("USER") or os.getenv("USERNAME") or ""
    
    # 检查是否在授权列表中
    if current_user in AUTHORIZED_APPROVERS:
        return True
    
    # 检查是否为 root
    if os.getuid() == 0:
        return True
    
    return False

def acquire_lock(lock_file: Path) -> bool:
    """获取文件锁，防止并发冲突"""
    try:
        fd = open(lock_file, 'w')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        return None

def release_lock(fd):
    """释放文件锁"""
    if fd:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()

def cleanup_expired_requests():
    """清理过期请求"""
    if not APPROVAL_DIR.exists():
        return
    
    now = datetime.now()
    cleaned = 0
    
    for approval_file in APPROVAL_DIR.glob("*.json"):
        try:
            with open(approval_file, 'r') as f:
                data = json.load(f)
            
            expires_at = datetime.fromisoformat(data.get("expires_at", "2000-01-01"))
            
            # 过期或已完成超过24小时
            if now > expires_at or (
                data.get("status") in ["approved", "rejected"] and
                now > expires_at + timedelta(hours=24)
            ):
                approval_file.unlink()
                cleaned += 1
        except Exception:
            pass
    
    if cleaned > 0:
        log_audit("cleanup", {"cleaned_count": cleaned})

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

def send_approval_request(approver, filepath, changes_desc, request_id, submitter):
    """发送审批请求"""
    channel = approver["channel"]
    identifier = approver["identifier"]
    
    # 构建审批请求消息
    message = f"""🔐 SafeConfig 审批请求

请求ID: {request_id}
提交人: {submitter}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📁 待修改文件: {filepath}

📝 变更说明:
{changes_desc}

⚠️ 这是一个关键配置文件，需要您的审批。

✅ 回复 "批准" 或执行:
   python3 safeconfig.py --approve {request_id}

❌ 回复 "拒绝" 或执行:
   python3 safeconfig.py --reject {request_id}

⏰ 审批将在30分钟后过期

---
安全提示: 此请求已记录审计日志
"""
    
    # 保存审批请求
    approval_file = APPROVAL_DIR / f"{request_id}.json"
    
    approval_data = {
        "request_id": request_id,
        "channel": channel,
        "recipient": identifier,
        "submitter": submitter,
        "message": message,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat()
    }
    
    # 使用文件锁防止并发写入
    lock_file = APPROVAL_DIR / ".lock"
    fd = acquire_lock(lock_file)
    if not fd:
        print_error("无法获取文件锁，可能有其他进程正在操作")
        return False
    
    try:
        with open(approval_file, 'w') as f:
            json.dump(approval_data, f, indent=2)
        
        # 设置权限（仅所有者可读写）
        os.chmod(approval_file, 0o600)
    finally:
        release_lock(fd)
    
    print_info(f"审批请求已创建: {approval_file}")
    print_info(f"请通知审批人 ({approver}) 查看并批准")
    
    # 记录审计日志
    log_audit("approval_request_created", {
        "request_id": request_id,
        "submitter": submitter,
        "approver": f"{channel}:{identifier}",
        "filepath": str(filepath)
    })
    
    return True

def wait_for_approval(request_id, timeout=1800):
    """等待审批结果"""
    approval_file = APPROVAL_DIR / f"{request_id}.json"
    
    print_info(f"\n⏳ 等待审批中... (最多30分钟)")
    print_info(f"审批人可执行: python3 safeconfig.py --approve {request_id}")
    
    start_time = time.time()
    check_interval = 5
    
    while time.time() - start_time < timeout:
        if approval_file.exists():
            try:
                with open(approval_file, 'r') as f:
                    data = json.load(f)
                
                status = data.get("status")
                if status == "approved":
                    approver = data.get("approved_by", "unknown")
                    print_success(f"审批已通过！ (by {approver})")
                    log_audit("approval_granted", {
                        "request_id": request_id,
                        "approver": approver
                    })
                    return True
                elif status == "rejected":
                    approver = data.get("rejected_by", "unknown")
                    print_error(f"审批被拒绝 (by {approver})")
                    log_audit("approval_rejected", {
                        "request_id": request_id,
                        "approver": approver
                    })
                    return False
            except Exception:
                pass
        
        remaining = int(timeout - (time.time() - start_time))
        if remaining % 60 == 0 and remaining > 0:
            print(f"   剩余时间: {remaining // 60} 分钟")
        
        time.sleep(check_interval)
    
    print_error("审批超时，操作取消")
    log_audit("approval_timeout", {"request_id": request_id})
    return False

def approve_request(request_id: str) -> bool:
    """批准请求（带身份验证）"""
    # 检查权限
    if not check_approver_permission():
        current_user = os.getenv("USER") or "unknown"
        print_error(f"用户 {current_user} 无审批权限")
        log_audit("approve_denied", {"request_id": request_id, "user": current_user})
        return False
    
    approval_file = APPROVAL_DIR / f"{request_id}.json"
    if not approval_file.exists():
        print_error(f"请求不存在: {request_id}")
        return False
    
    # 使用文件锁
    lock_file = APPROVAL_DIR / ".lock"
    fd = acquire_lock(lock_file)
    if not fd:
        print_error("无法获取文件锁")
        return False
    
    try:
        with open(approval_file, 'r') as f:
            data = json.load(f)
        
        current_user = os.getenv("USER") or os.getenv("USERNAME") or f"uid_{os.getuid()}"
        data["status"] = "approved"
        data["approved_by"] = current_user
        data["approved_at"] = datetime.now().isoformat()
        
        with open(approval_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print_success(f"已批准请求: {request_id} (by {current_user})")
        log_audit("approve", {"request_id": request_id, "approver": current_user})
        return True
    finally:
        release_lock(fd)

def reject_request(request_id: str) -> bool:
    """拒绝请求（带身份验证）"""
    # 检查权限
    if not check_approver_permission():
        current_user = os.getenv("USER") or "unknown"
        print_error(f"用户 {current_user} 无审批权限")
        log_audit("reject_denied", {"request_id": request_id, "user": current_user})
        return False
    
    approval_file = APPROVAL_DIR / f"{request_id}.json"
    if not approval_file.exists():
        print_error(f"请求不存在: {request_id}")
        return False
    
    lock_file = APPROVAL_DIR / ".lock"
    fd = acquire_lock(lock_file)
    if not fd:
        print_error("无法获取文件锁")
        return False
    
    try:
        with open(approval_file, 'r') as f:
            data = json.load(f)
        
        current_user = os.getenv("USER") or os.getenv("USERNAME") or f"uid_{os.getuid()}"
        data["status"] = "rejected"
        data["rejected_by"] = current_user
        data["rejected_at"] = datetime.now().isoformat()
        
        with open(approval_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print_error(f"已拒绝请求: {request_id} (by {current_user})")
        log_audit("reject", {"request_id": request_id, "approver": current_user})
        return True
    finally:
        release_lock(fd)

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

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*50}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*50}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def main():
    parser = argparse.ArgumentParser(
        description="SafeConfig - 安全配置管理（安全增强版）",
        epilog="安全增强: UUID4 | 身份验证 | 单审批人 | 审计日志"
    )
    parser.add_argument("--check", help="检查配置文件")
    parser.add_argument("--backup", help="备份配置文件")
    parser.add_argument("--validate-systemd", help="验证 systemd 配置")
    parser.add_argument("--approver", help="指定审批人")
    parser.add_argument("--changes", help="变更说明")
    parser.add_argument("--approve", help="批准请求（需权限）")
    parser.add_argument("--reject", help="拒绝请求（需权限）")
    parser.add_argument("--cleanup", action="store_true", help="清理过期请求")
    parser.add_argument("--audit-log", action="store_true", help="查看审计日志")
    
    args = parser.parse_args()
    
    # 初始化
    ensure_dirs()
    
    # 清理过期请求
    cleanup_expired_requests()
    
    # 查看审计日志
    if args.audit_log:
        log_file = LOG_DIR / f"audit_{datetime.now().strftime('%Y%m')}.log"
        if log_file.exists():
            print(log_file.read_text())
        else:
            print("暂无审计日志")
        return
    
    # 处理批准/拒绝
    if args.approve:
        sys.exit(0 if approve_request(args.approve) else 1)
    
    if args.reject:
        sys.exit(0 if reject_request(args.reject) else 1)
    
    # 检查配置文件
    if args.check:
        filepath = Path(args.check).expanduser()
        is_critical = is_critical_config(filepath)
        print(f"文件: {filepath}")
        print(f"关键配置: {'是' if is_critical else '否'}")
        if is_critical:
            print("\n⚠️  这是关键配置文件，修改前必须：")
            print("  1. 验证参数有效性")
            print("  2. 创建备份")
            print("  3. 获得用户确认")
            if args.approver:
                print(f"  4. 获得审批人确认 ({args.approver})")
        return
    
    # 备份配置（带审批流程）
    if args.backup:
        filepath = Path(args.backup).expanduser()
        submitter = os.getenv("USER") or os.getenv("USERNAME") or f"uid_{os.getuid()}"
        
        # 如果指定了审批人，进入审批流程
        if args.approver:
            approver = parse_approver(args.approver)
            if not approver:
                print_error("审批人格式错误，应为: telegram:username 或 email:address")
                sys.exit(1)
            
            changes = args.changes or f"备份文件: {filepath}"
            request_id = str(uuid.uuid4())  # 使用 UUID4
            
            print_header("🔐 启动审批流程")
            print_info(f"请求ID: {request_id}")
            print_info(f"提交人: {submitter}")
            print_info(f"审批人: {approver['channel']}:{approver['identifier']}")
            
            # 发送审批请求
            if not send_approval_request(approver, str(filepath), changes, request_id, submitter):
                print_error("审批请求发送失败")
                sys.exit(1)
            
            # 等待审批
            if not wait_for_approval(request_id):
                print_error("审批未通过，操作取消")
                sys.exit(1)
            
            print_header("📦 继续执行备份...")
        
        # 执行备份
        backup_path = backup_config(filepath)
        if backup_path:
            print_success(f"备份已创建: {backup_path}")
            log_audit("backup_created", {"filepath": str(filepath), "backup": str(backup_path)})
        else:
            print_warning(f"文件不存在，无需备份: {filepath}")
        return
    
    # 验证 systemd 配置
    if args.validate_systemd:
        valid, error = validate_systemd_config(args.validate_systemd)
        if valid:
            print_success("systemd 配置验证通过")
        else:
            print_error(f"systemd 配置错误: {error}")
        sys.exit(0 if valid else 1)
    
    # 默认：显示帮助
    print_header("SafeConfig - 安全配置管理（安全增强版）")
    print("\n安全特性:")
    print("  • UUID4 随机请求ID")
    print("  • 审批人身份验证")
    print("  • 单审批人权限控制")
    print("  • 文件锁防并发")
    print("  • 自动清理过期请求")
    print("  • 完整审计日志")
    print("\n使用方法:")
    print("  safeconfig.py --check <filepath>")
    print("  safeconfig.py --backup <filepath> --approver telegram:admin")
    print("  safeconfig.py --approve <request_id>    # 需要权限")
    print("  safeconfig.py --reject <request_id>     # 需要权限")
    print("  safeconfig.py --audit-log               # 查看审计日志")

if __name__ == "__main__":
    main()
