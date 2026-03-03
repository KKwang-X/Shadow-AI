#!/usr/bin/env python3
"""
Pre-Deploy Check - 部署前验证脚本
验证所有关键配置文件，避免上线即崩溃
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# 关键配置文件列表
CONFIG_CHECKS = [
    {
        "name": "OpenClaw Config",
        "file": "~/.openclaw/openclaw.json",
        "type": "json",
        "critical": True
    },
    {
        "name": "Systemd Service",
        "file": "/etc/systemd/system/openclaw.service",
        "type": "systemd",
        "critical": True
    },
    {
        "name": "QQMail Config",
        "file": "~/.openclaw/workspace/skills/qqmail-sender/config.json",
        "type": "json",
        "critical": False
    },
    {
        "name": "SafeConfig Approvals",
        "file": "~/.safeconfig",
        "type": "directory",
        "critical": False
    }
]

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def check_json_syntax(filepath):
    """检查 JSON 语法"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True, "JSON 语法正确"
    except json.JSONDecodeError as e:
        return False, f"JSON 语法错误: {e}"
    except FileNotFoundError:
        return False, "文件不存在"
    except Exception as e:
        return False, str(e)

def check_systemd_config(filepath):
    """检查 Systemd 配置"""
    try:
        result = subprocess.run(
            ["systemd-analyze", "verify", str(filepath)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "Systemd 配置正确"
        else:
            return False, f"Systemd 配置错误: {result.stderr}"
    except FileNotFoundError:
        return False, "文件不存在"
    except Exception as e:
        return False, str(e)

def check_openclaw_params():
    """检查 OpenClaw 参数有效性"""
    issues = []
    
    # 读取 openclaw.json
    config_path = Path("~/.openclaw/openclaw.json").expanduser()
    if not config_path.exists():
        return False, ["配置文件不存在"]
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        return False, [f"无法读取配置: {e}"]
    
    # 检查关键字段
    checks = [
        ("channels.telegram.botToken", "Telegram Bot Token 配置"),
        ("gateway.auth.token", "Gateway Auth Token"),
    ]
    
    for path, desc in checks:
        keys = path.split('.')
        value = config
        try:
            for key in keys:
                value = value[key]
            if not value or value == "YOUR_TOKEN_HERE":
                issues.append(f"{desc} 未配置或为空")
        except (KeyError, TypeError):
            issues.append(f"{desc} 缺失")
    
    # 检查 systemd 服务中的参数
    service_path = Path("/etc/systemd/system/openclaw.service")
    if service_path.exists():
        try:
            content = service_path.read_text()
            # 检查是否使用了不存在的参数
            if "--daemon" in content:
                issues.append("Systemd 服务使用了不存在的 --daemon 参数")
        except Exception as e:
            issues.append(f"无法读取服务文件: {e}")
    
    if issues:
        return False, issues
    return True, ["所有参数检查通过"]

def check_service_status():
    """检查服务状态（dry-run）"""
    try:
        result = subprocess.run(
            ["systemctl", "status", "openclaw", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "OpenClaw 服务运行正常"
        elif "inactive" in result.stdout or "failed" in result.stdout:
            return False, "OpenClaw 服务未运行或已失败"
        else:
            return True, "OpenClaw 服务状态需检查"
    except Exception as e:
        return False, f"无法检查服务状态: {e}"

def check_gateway_connectivity():
    """检查 Gateway 连接性"""
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if "running" in result.stdout.lower() or result.returncode == 0:
            return True, "Gateway 响应正常"
        else:
            return False, f"Gateway 状态异常: {result.stderr}"
    except Exception as e:
        return False, f"无法连接 Gateway: {e}"

def run_all_checks():
    """运行所有检查"""
    print_header("🚀 Pre-Deploy Check - 部署前验证")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "details": []
    }
    
    # 1. 配置文件语法检查
    print_header("📁 配置文件语法检查")
    for check in CONFIG_CHECKS:
        filepath = Path(check["file"]).expanduser()
        print(f"\n检查: {check['name']} ({filepath})")
        
        if check["type"] == "json":
            success, msg = check_json_syntax(filepath)
        elif check["type"] == "systemd":
            success, msg = check_systemd_config(filepath)
        elif check["type"] == "directory":
            success = filepath.exists()
            msg = "目录存在" if success else "目录不存在（将自动创建）"
        else:
            success = filepath.exists()
            msg = "文件存在" if success else "文件不存在"
        
        if success:
            print_success(msg)
            results["passed"] += 1
        else:
            if check["critical"]:
                print_error(msg)
                results["failed"] += 1
            else:
                print_warning(msg)
                results["warnings"] += 1
        
        results["details"].append({
            "name": check["name"],
            "success": success,
            "message": msg,
            "critical": check["critical"]
        })
    
    # 2. 参数有效性检查
    print_header("🔍 参数有效性检查")
    success, issues = check_openclaw_params()
    for issue in issues:
        if success:
            print_success(issue)
            results["passed"] += 1
        else:
            print_error(issue)
            results["failed"] += 1
    
    # 3. 服务状态检查
    print_header("🔧 服务状态检查")
    success, msg = check_service_status()
    if success:
        print_success(msg)
        results["passed"] += 1
    else:
        print_warning(msg)  # 服务未运行不一定是错误
        results["warnings"] += 1
    
    # 4. Gateway 连接性
    print_header("🌐 Gateway 连接性检查")
    success, msg = check_gateway_connectivity()
    if success:
        print_success(msg)
        results["passed"] += 1
    else:
        print_warning(msg)
        results["warnings"] += 1
    
    # 总结报告
    print_header("📊 检查报告")
    print(f"通过: {Colors.GREEN}{results['passed']}{Colors.RESET}")
    print(f"失败: {Colors.RED}{results['failed']}{Colors.RESET}")
    print(f"警告: {Colors.YELLOW}{results['warnings']}{Colors.RESET}")
    
    if results["failed"] > 0:
        print(f"\n{Colors.RED}❌ 部署检查未通过，请修复上述错误后再部署{Colors.RESET}")
        return 1
    elif results["warnings"] > 0:
        print(f"\n{Colors.YELLOW}⚠️  部署检查通过，但有警告项，建议查看{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.GREEN}✅ 所有检查通过，可以安全部署{Colors.RESET}")
        return 0

def main():
    try:
        exit_code = run_all_checks()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  检查被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ 检查过程出错: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
