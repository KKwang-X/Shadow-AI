#!/usr/bin/env python3
"""
SafeDeploy - 安全部署工具
踩过无数坑换来的 OpenClaw 部署神器

血泪教训换来的功能：
- 曾因 --daemon 参数崩溃 3 次
- 曾因配置语法错误导致服务无法启动
- 曾因未备份配置丢失重要设置
- 曾因未测试直接上线引发故障

本工具 = Pre-Deploy Check + SafeConfig + 自动修复 + 审批流程
"""

import sys
import os
import json
import shutil
import subprocess
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}🔧 {text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

# 关键配置定义
CRITICAL_CONFIGS = [
    {
        "name": "OpenClaw Config",
        "path": "~/.openclaw/openclaw.json",
        "type": "json",
        "critical": True,
        "auto_fix": True
    },
    {
        "name": "Systemd Service",
        "path": "/etc/systemd/system/openclaw.service",
        "type": "systemd",
        "critical": True,
        "auto_fix": True
    },
    {
        "name": "QQMail Config",
        "path": "~/.openclaw/workspace/skills/qqmail-sender/config.json",
        "type": "json",
        "critical": False,
        "auto_fix": False
    }
]

# 已知的无效参数（血泪教训）
INVALID_PARAMS = [
    "--daemon",  # 坑 #1: 曾因此崩溃 3 次
    "--debug-mode",  # 不存在的参数
    "--verbose-level",  # 不存在的参数
]

# 审批目录
APPROVAL_DIR = Path("~/.safeconfig/approvals").expanduser()
BACKUP_DIR = Path("~/.config-backups").expanduser()

class SafeDeploy:
    def __init__(self):
        self.issues = []
        self.fixes = []
        self.changes = []
        
    def ensure_dirs(self):
        """确保必要目录存在"""
        APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    def check_json_syntax(self, filepath: Path) -> Tuple[bool, str, Optional[dict]]:
        """检查 JSON 语法，返回 (是否成功, 消息, 解析后的数据)"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return True, "JSON 语法正确", data
        except json.JSONDecodeError as e:
            return False, f"JSON 语法错误: {e}", None
        except FileNotFoundError:
            return False, "文件不存在", None
        except Exception as e:
            return False, str(e), None
    
    def fix_json_syntax(self, filepath: Path) -> Tuple[bool, str]:
        """尝试修复 JSON 语法错误"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # 常见修复：去除尾随逗号
            import re
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            # 尝试解析
            data = json.loads(content)
            
            # 写回修复后的内容
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True, "已修复 JSON 语法错误（去除尾随逗号）"
        except Exception as e:
            return False, f"无法修复: {e}"
    
    def check_systemd_config(self, filepath: Path) -> Tuple[bool, str]:
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
        except Exception as e:
            return False, str(e)
    
    def fix_systemd_config(self, filepath: Path) -> Tuple[bool, str]:
        """修复 Systemd 配置中的常见问题"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            original = content
            fixes = []
            
            # 修复 #1: 移除 --daemon 参数（血泪教训）
            for param in INVALID_PARAMS:
                if param in content:
                    content = content.replace(f" {param}", "")
                    content = content.replace(param, "")
                    fixes.append(f"移除无效参数 {param}")
            
            if content != original:
                with open(filepath, 'w') as f:
                    f.write(content)
                return True, f"已修复: {', '.join(fixes)}"
            
            return False, "无需修复"
        except Exception as e:
            return False, f"修复失败: {e}"
    
    def check_openclaw_params(self, data: dict) -> Tuple[bool, List[str]]:
        """检查 OpenClaw 参数有效性"""
        issues = []
        
        # 检查关键字段
        if not data.get("channels", {}).get("telegram", {}).get("botToken"):
            issues.append("Telegram Bot Token 未配置")
        
        if not data.get("gateway", {}).get("auth", {}).get("token"):
            issues.append("Gateway Auth Token 未配置")
        
        # 检查无效参数（在 systemd 服务中）
        service_path = Path("/etc/systemd/system/openclaw.service")
        if service_path.exists():
            content = service_path.read_text()
            for param in INVALID_PARAMS:
                if param in content:
                    issues.append(f"Systemd 服务包含无效参数 {param}")
        
        return len(issues) == 0, issues
    
    def validate_all(self, auto_fix: bool = False) -> bool:
        """验证所有配置"""
        print_header("部署前验证 - 踩过无数坑的安全检查")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"模式: {'自动修复' if auto_fix else '仅检查'}\n")
        
        all_passed = True
        
        for config in CRITICAL_CONFIGS:
            filepath = Path(config["path"]).expanduser()
            print(f"\n📁 检查: {config['name']}")
            print(f"   路径: {filepath}")
            
            if not filepath.exists():
                if config["critical"]:
                    print_error(f"关键文件不存在: {filepath}")
                    all_passed = False
                else:
                    print_warning(f"文件不存在（可选）: {filepath}")
                continue
            
            # 根据类型检查
            if config["type"] == "json":
                success, msg, data = self.check_json_syntax(filepath)
                if not success and auto_fix and config.get("auto_fix"):
                    fix_success, fix_msg = self.fix_json_syntax(filepath)
                    if fix_success:
                        print_success(f"自动修复: {fix_msg}")
                        self.fixes.append(f"{config['name']}: {fix_msg}")
                        success, msg, data = self.check_json_syntax(filepath)
                    else:
                        print_error(f"无法修复: {fix_msg}")
                
                if success:
                    print_success(msg)
                    # 额外检查 OpenClaw 参数
                    if config["name"] == "OpenClaw Config" and data:
                        param_ok, issues = self.check_openclaw_params(data)
                        if not param_ok:
                            for issue in issues:
                                print_error(f"参数问题: {issue}")
                                all_passed = False
                        else:
                            print_success("所有参数检查通过")
                else:
                    print_error(msg)
                    all_passed = False
                    
            elif config["type"] == "systemd":
                success, msg = self.check_systemd_config(filepath)
                if not success and auto_fix and config.get("auto_fix"):
                    fix_success, fix_msg = self.fix_systemd_config(filepath)
                    if fix_success:
                        print_success(f"自动修复: {fix_msg}")
                        self.fixes.append(f"{config['name']}: {fix_msg}")
                        # 重新检查
                        success, msg = self.check_systemd_config(filepath)
                    else:
                        if "无需修复" not in fix_msg:
                            print_error(f"无法修复: {fix_msg}")
                
                if success:
                    print_success(msg)
                else:
                    print_error(msg)
                    all_passed = False
        
        return all_passed
    
    def create_backup(self, filepath: Path) -> Optional[Path]:
        """创建配置备份"""
        if not filepath.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"{filepath.name}.{timestamp}.bak"
        
        shutil.copy2(filepath, backup_path)
        return backup_path
    
    def send_approval_request(self, approver: str, changes: str, request_id: str) -> bool:
        """发送审批请求"""
        self.ensure_dirs()
        approval_file = APPROVAL_DIR / f"{request_id}.json"
        
        # 解析审批人
        if ":" in approver:
            channel, identifier = approver.split(":", 1)
        else:
            print_error("审批人格式错误，应为: telegram:username 或 email:address")
            return False
        
        message = f"""🔐 SafeDeploy 审批请求

请求ID: {request_id}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 变更说明:
{changes}

🔧 自动修复记录:
{chr(10).join(self.fixes) if self.fixes else "无"}

⚠️ 这是一个关键配置变更，需要您的审批。

✅ 回复 "批准" 或执行:
   python3 safedeploy.py --approve {request_id}

❌ 回复 "拒绝" 或执行:
   python3 safedeploy.py --reject {request_id}

⏰ 审批将在30分钟后过期
"""
        
        approval_data = {
            "request_id": request_id,
            "channel": channel,
            "recipient": identifier,
            "message": message,
            "changes": changes,
            "fixes": self.fixes,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        
        with open(approval_file, 'w') as f:
            json.dump(approval_data, f, indent=2)
        
        print_info(f"审批请求已创建: {approval_file}")
        print_info(f"请通知审批人 ({approver}) 查看并批准")
        
        # 尝试发送通知（如果配置了 QQMail）
        try:
            qqmail_path = Path(__file__).parent / "skills" / "qqmail-sender" / "qqmail.py"
            if channel == "email" and qqmail_path.exists():
                subprocess.run([
                    "python3", str(qqmail_path),
                    identifier,
                    f"🔐 SafeDeploy 审批请求 - {request_id}",
                    message
                ], check=True)
                print_success(f"审批邮件已发送至 {identifier}")
        except Exception as e:
            print_warning(f"邮件发送失败: {e}")
        
        return True
    
    def wait_for_approval(self, request_id: str, timeout: int = 1800) -> bool:
        """等待审批结果"""
        approval_file = APPROVAL_DIR / f"{request_id}.json"
        
        print_info(f"\n⏳ 等待审批中... (最多30分钟)")
        print_info(f"审批人可修改文件后保存: {approval_file}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if approval_file.exists():
                with open(approval_file, 'r') as f:
                    data = json.load(f)
                
                status = data.get("status")
                if status == "approved":
                    print_success("审批已通过！")
                    return True
                elif status == "rejected":
                    print_error("审批被拒绝")
                    return False
            
            remaining = int(timeout - (time.time() - start_time))
            if remaining % 60 == 0:
                print(f"   剩余时间: {remaining // 60} 分钟")
            
            time.sleep(5)
        
        print_error("审批超时，操作取消")
        return False
    
    def approve(self, request_id: str):
        """批准请求"""
        approval_file = APPROVAL_DIR / f"{request_id}.json"
        if not approval_file.exists():
            print_error(f"请求不存在: {request_id}")
            return False
        
        with open(approval_file, 'r') as f:
            data = json.load(f)
        
        data["status"] = "approved"
        data["approved_at"] = datetime.now().isoformat()
        
        with open(approval_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print_success(f"已批准请求: {request_id}")
        return True
    
    def reject(self, request_id: str):
        """拒绝请求"""
        approval_file = APPROVAL_DIR / f"{request_id}.json"
        if not approval_file.exists():
            print_error(f"请求不存在: {request_id}")
            return False
        
        with open(approval_file, 'r') as f:
            data = json.load(f)
        
        data["status"] = "rejected"
        data["rejected_at"] = datetime.now().isoformat()
        
        with open(approval_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print_error(f"已拒绝请求: {request_id}")
        return True
    
    def generate_report(self):
        """生成部署报告"""
        print_header("部署报告")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.fixes:
            print(f"\n🔧 自动修复 ({len(self.fixes)} 项):")
            for fix in self.fixes:
                print(f"   ✅ {fix}")
        
        print(f"\n📊 检查结果:")
        print(f"   通过: {Colors.GREEN}✅{Colors.RESET}")
        print(f"   失败: {Colors.RED}❌{Colors.RESET}")
        print(f"   警告: {Colors.YELLOW}⚠️{Colors.RESET}")

def main():
    parser = argparse.ArgumentParser(
        description="SafeDeploy - 踩过无数坑换来的 OpenClaw 安全部署工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
血泪教训:
  曾因 --daemon 参数崩溃 3 次
  曾因未备份配置丢失重要设置
  曾因未测试直接上线引发故障

本工具 = 验证 + 修复 + 审批 + 部署，确保万无一失。

示例:
  # 仅验证配置
  python3 safedeploy.py check
  
  # 验证并自动修复
  python3 safedeploy.py fix
  
  # 完整部署流程（含审批）
  python3 safedeploy.py deploy --approver telegram:admin
  
  # 批准/拒绝请求
  python3 safedeploy.py --approve req_xxx
  python3 safedeploy.py --reject req_xxx
        """
    )
    
    parser.add_argument("command", choices=["check", "fix", "deploy"], 
                       help="执行命令: check=仅检查, fix=检查并修复, deploy=完整部署")
    parser.add_argument("--approver", help="指定审批人 (格式: telegram:username 或 email:address)")
    parser.add_argument("--changes", help="变更说明")
    parser.add_argument("--approve", help="批准指定请求ID")
    parser.add_argument("--reject", help="拒绝指定请求ID")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认，不提示")
    
    args = parser.parse_args()
    
    deployer = SafeDeploy()
    deployer.ensure_dirs()
    
    # 处理批准/拒绝
    if args.approve:
        deployer.approve(args.approve)
        return
    
    if args.reject:
        deployer.reject(args.reject)
        return
    
    # 执行命令
    if args.command == "check":
        success = deployer.validate_all(auto_fix=False)
        deployer.generate_report()
        sys.exit(0 if success else 1)
    
    elif args.command == "fix":
        print_header("自动修复模式 - 发现即修复")
        success = deployer.validate_all(auto_fix=True)
        deployer.generate_report()
        
        if deployer.fixes:
            print(f"\n{Colors.GREEN}已自动修复 {len(deployer.fixes)} 个问题{Colors.RESET}")
        
        sys.exit(0 if success else 1)
    
    elif args.command == "deploy":
        print_header("完整部署流程")
        
        # 1. 验证并修复
        print_info("步骤 1/4: 验证配置...")
        success = deployer.validate_all(auto_fix=True)
        if not success:
            print_error("验证未通过，部署中止")
            sys.exit(1)
        
        # 2. 创建备份
        print_info("\n步骤 2/4: 创建备份...")
        for config in CRITICAL_CONFIGS:
            filepath = Path(config["path"]).expanduser()
            if filepath.exists():
                backup = deployer.create_backup(filepath)
                if backup:
                    print_success(f"备份: {backup}")
        
        # 3. 审批流程（如果指定了审批人）
        if args.approver:
            print_info("\n步骤 3/4: 审批流程...")
            changes = args.changes or f"自动修复: {', '.join(deployer.fixes) if deployer.fixes else '配置更新'}"
            request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
            
            if not deployer.send_approval_request(args.approver, changes, request_id):
                print_error("审批请求发送失败")
                sys.exit(1)
            
            if not deployer.wait_for_approval(request_id):
                print_error("审批未通过，部署中止")
                sys.exit(1)
        else:
            # 无审批人，需要用户确认
            if not args.yes:
                confirm = input(f"\n{Colors.YELLOW}确认部署? (yes/no): {Colors.RESET}")
                if confirm.lower() != "yes":
                    print_error("部署取消")
                    sys.exit(1)
        
        # 4. 执行部署
        print_info("\n步骤 4/4: 执行部署...")
        try:
            # 重启服务
            result = subprocess.run(
                ["sudo", "systemctl", "restart", "openclaw"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print_success("服务重启成功")
            else:
                print_error(f"服务重启失败: {result.stderr}")
                sys.exit(1)
            
            # 验证服务状态
            time.sleep(2)
            result = subprocess.run(
                ["systemctl", "is-active", "openclaw"],
                capture_output=True,
                text=True
            )
            if "active" in result.stdout:
                print_success("服务运行正常")
            else:
                print_error("服务状态异常")
                sys.exit(1)
            
            print_header("🎉 部署成功！")
            deployer.generate_report()
            
        except Exception as e:
            print_error(f"部署失败: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
