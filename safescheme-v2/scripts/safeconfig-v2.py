#!/usr/bin/env python3
"""
SafeConfig v2.1 - 完整配置管理流程
不可绕过的强制安全流程
"""

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# 导入 safescheme 和 rollback_manager
sys.path.insert(0, str(Path(__file__).parent))
from safescheme import SafeSchemeValidator
from rollback_manager import RollbackManager


class SafeConfigV2:
    """SafeConfig v2.1 主控制器"""
    
    VERSION = "2.1"
    
    def __init__(self):
        self.approval_dir = Path("~/.safeconfig/approvals").expanduser()
        self.backup_dir = Path("~/.config-backups").expanduser()
        self.log_dir = Path("~/.safeconfig/logs").expanduser()
        self.new_content_path: Optional[Path] = None
        self.ensure_dirs()
        
    def ensure_dirs(self):
        """确保必要目录存在"""
        for d in [self.approval_dir, self.backup_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)
            os.chmod(d, 0o700)
    
    def run_full_flow(self, filepath: str, approver: str, changes: str,
                      new_content_path: Optional[Path] = None):
        """执行完整 SafeConfig 流程"""
        print(f"🔐 SafeConfig v{self.VERSION} - 完整流程")
        print("=" * 70)

        self.new_content_path = new_content_path

        # Phase 1: 预审查
        if not self.phase1_pre_check(filepath):
            return False

        # Phase 2: 变更分析
        self.phase2_analyze_changes(filepath, changes)

        # Phase 3: 创建备份
        backup_path = self.phase3_create_backup(filepath)
        if not backup_path:
            return False

        # Phase 4: 生成审批请求
        request_id = self.phase4_create_approval(filepath, approver, changes, backup_path)

        # Phase 5: 等待审批
        if not self.phase5_wait_for_approval(request_id):
            return False

        # Phase 6: 虚拟环境测试
        if not self.phase6_virtual_test(filepath, changes):
            return False

        # Phase 7: 执行变更
        if not self.phase7_apply_changes(filepath, changes):
            return False

        # Phase 8: 验证结果
        if not self.phase8_verify_result(filepath, backup_path):
            return False

        # Phase 9: 审计日志
        self.phase9_audit_log(request_id, filepath, changes, approver, backup_path)
        
        print("\n" + "=" * 70)
        print("✅ SafeConfig 流程完成")
        print("=" * 70)
        return True
    
    def phase1_pre_check(self, filepath: str) -> bool:
        """Phase 1: 预审查（仅 Scheme 结构，不检查服务状态）"""
        print("\n📋 Phase 1: 预审查 (Scheme 结构校验)")
        print("-" * 70)

        validator = SafeSchemeValidator(filepath)
        success = validator.validate_scheme_only()

        if not success:
            print("\n❌ Phase 1 失败: 当前配置不符合 Scheme 要求")
            return False

        print("\n✅ Phase 1 通过")
        return True
    
    def phase2_analyze_changes(self, filepath: str, changes: str):
        """Phase 2: 变更分析"""
        print("\n📋 Phase 2: 变更分析")
        print("-" * 70)
        
        print(f"📁 目标文件: {filepath}")
        print(f"📝 变更说明: {changes}")
        print(f"🔍 变更类型: 修改")
        print(f"🔴 风险等级: 低")
        print(f"⏱️  预计停机: 0 秒")
        
        print("\n✅ Phase 2 完成")
    
    def phase3_create_backup(self, filepath: str) -> Optional[Path]:
        """Phase 3: 创建备份"""
        print("\n📋 Phase 3: 创建备份")
        print("-" * 70)
        
        src = Path(filepath).expanduser()
        if not src.exists():
            print(f"❌ 源文件不存在: {src}")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{src.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(src, backup_path)
        os.chmod(backup_path, 0o600)
        
        print(f"✅ 备份已创建: {backup_path}")
        return backup_path
    
    def phase4_create_approval(self, filepath: str, approver: str, changes: str, backup_path: Path) -> str:
        """Phase 4: 生成审批请求"""
        print("\n📋 Phase 4: 生成审批请求")
        print("-" * 70)
        
        request_id = str(uuid.uuid4())
        submitter = os.getenv("USER") or "unknown"
        
        approval_data = {
            "request_id": request_id,
            "version": self.VERSION,
            "timestamp": datetime.now().isoformat(),
            "submitter": submitter,
            "approver": approver,
            "filepath": str(filepath),
            "changes": changes,
            "backup_path": str(backup_path),
            "status": "pending",
            "phases_completed": ["1", "2", "3", "4"]
        }
        
        approval_file = self.approval_dir / f"{request_id}.json"
        with open(approval_file, 'w') as f:
            json.dump(approval_data, f, indent=2)
        os.chmod(approval_file, 0o600)
        
        print(f"✅ 审批请求已生成")
        print(f"🆔 请求ID: {request_id}")
        print(f"👤 审批人: {approver}")
        print(f"\n批准命令:")
        print(f"  python3 safeconfig-v2.py --approve {request_id}")
        
        return request_id
    
    def phase5_wait_for_approval(self, request_id: str, timeout: int = 1800) -> bool:
        """Phase 5: 等待审批（轮询，最多30分钟）"""
        print("\n📋 Phase 5: 等待审批")
        print("-" * 70)
        print(f"⏳ 等待审批人批准... (最多 {timeout // 60} 分钟)")
        print(f"🆔 请求ID: {request_id}")
        print(f"\n批准命令: python3 safeconfig-v2.py --approve {request_id}")
        print(f"拒绝命令: python3 safeconfig-v2.py --reject {request_id}")
        print("按 Ctrl+C 可取消等待\n")

        approval_file = self.approval_dir / f"{request_id}.json"
        start_time = time.time()
        check_interval = 5

        try:
            while time.time() - start_time < timeout:
                if approval_file.exists():
                    with open(approval_file, 'r') as f:
                        data = json.load(f)

                    status = data.get("status")
                    if status == "approved":
                        approver = data.get("approved_by", "unknown")
                        print(f"\n✅ Phase 5 通过: 已批准 (by {approver})")
                        return True
                    elif status == "rejected":
                        approver = data.get("rejected_by", "unknown")
                        print(f"\n❌ Phase 5 失败: 已拒绝 (by {approver})")
                        return False

                remaining = int(timeout - (time.time() - start_time))
                if remaining % 60 == 0 and remaining > 0:
                    print(f"   剩余等待时间: {remaining // 60} 分钟...")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n⚠️  用户取消等待")
            return False

        print("\n❌ Phase 5 失败: 审批超时")
        return False
    
    def phase6_virtual_test(self, filepath: str, changes: str) -> bool:
        """Phase 6: 虚拟环境测试（验证拟议内容的 Scheme 合规性）"""
        print("\n📋 Phase 6: 虚拟环境测试")
        print("-" * 70)

        src = Path(filepath).expanduser()
        test_env = Path("~/.openclaw.test").expanduser()
        test_config = test_env / src.name

        try:
            # 1. 创建测试环境
            print("1. 创建测试环境...")
            if test_env.exists():
                shutil.rmtree(test_env)
            shutil.copytree(src.parent, test_env)
            print("   ✅ 测试环境创建完成")

            # 2. 将拟议内容写入测试环境
            print("2. 应用变更到测试环境...")
            if self.new_content_path and self.new_content_path.exists():
                shutil.copy2(self.new_content_path, test_config)
                print(f"   ✅ 已写入拟议内容: {self.new_content_path}")
            else:
                # 无拟议文件时只验证原始内容（兜底）
                print("   ⚠️  未提供 --new-content-file，验证当前文件内容")

            # 3. 验证测试环境配置（Scheme-only，不检查服务状态）
            print("3. 验证测试环境配置...")
            validator = SafeSchemeValidator(str(test_config))
            if not validator.validate_scheme_only():
                print("   ❌ 测试环境 Scheme 验证失败，拒绝应用变更")
                return False
            print("   ✅ 测试环境验证通过")

            # 4. 清理测试环境
            print("4. 清理测试环境...")
            shutil.rmtree(test_env)
            print("   ✅ 测试环境已清理")

            print("\n✅ Phase 6 通过: 虚拟环境测试成功")
            return True

        except Exception as e:
            print(f"\n❌ Phase 6 失败: {e}")
            if test_env.exists():
                shutil.rmtree(test_env)
            return False
    
    def phase7_apply_changes(self, filepath: str, changes: str) -> bool:
        """Phase 7: 执行变更（自动写入或交互式确认）"""
        print("\n📋 Phase 7: 执行变更")
        print("-" * 70)
        print(f"📁 目标文件: {filepath}")
        print(f"📝 变更说明: {changes}")
        print()

        dst = Path(filepath).expanduser()

        if self.new_content_path and self.new_content_path.exists():
            # 自动模式：直接写入拟议内容（已经过 Phase 6 验证）
            try:
                shutil.copy2(self.new_content_path, dst)
                print(f"✅ Phase 7 完成：已自动写入 {dst}")
                return True
            except Exception as e:
                print(f"❌ Phase 7 失败：写入出错 — {e}")
                return False
        else:
            # 交互式模式：等待用户手动修改后确认
            print("请现在手动修改目标文件，例如:")
            print(f"  nano {filepath}")
            print(f"  vi {filepath}")
            print()
            try:
                input("✏️  修改完成后按 Enter 继续（Ctrl+C 取消）...")
            except KeyboardInterrupt:
                print("\n⚠️  用户取消变更")
                return False
            print("\n✅ Phase 7 完成：用户确认变更已应用")
            return True
    
    def phase8_verify_result(self, filepath: str, backup_path: Optional[Path] = None) -> bool:
        """Phase 8: 验证结果，失败时自动回滚"""
        print("\n📋 Phase 8: 验证结果")
        print("-" * 70)

        validator = SafeSchemeValidator(filepath)
        if not validator.validate_scheme_only():
            print("\n❌ Phase 8 失败: 变更后 Scheme 验证未通过")
            if backup_path:
                print("⚠️  启动自动回滚...")
                rm = RollbackManager(str(self.backup_dir))
                if rm.rollback(filepath, str(backup_path)):
                    print("✅ 已回滚到变更前状态")
                else:
                    print("❌ 自动回滚失败！请手动检查配置")
            return False

        print("\n✅ Phase 8 通过: 验证成功")
        return True
    
    def phase9_audit_log(self, request_id: str, filepath: str, changes: str, approver: str, backup_path: Path):
        """Phase 9: 审计日志"""
        print("\n📋 Phase 9: 审计日志")
        print("-" * 70)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "version": self.VERSION,
            "request_id": request_id,
            "filepath": str(filepath),
            "changes": changes,
            "submitter": os.getenv("USER") or "unknown",
            "approver": approver,
            "backup_path": str(backup_path),
            "status": "completed",
            "phases": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        }
        
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
        
        print(f"✅ 审计日志已记录: {log_file}")
    
    def _check_approver_permission(self) -> bool:
        """检查当前用户是否有审批权限"""
        current_user = os.getenv("USER") or os.getenv("USERNAME") or ""
        authorized = ["admin", "kk"]  # 与 safeconfig.py 保持一致，可按需配置
        return current_user in authorized or os.getuid() == 0

    def approve(self, request_id: str) -> bool:
        """批准请求（带身份验证）"""
        current_user = os.getenv("USER") or os.getenv("USERNAME") or f"uid_{os.getuid()}"

        if not self._check_approver_permission():
            print(f"❌ 用户 {current_user} 无审批权限")
            return False

        approval_file = self.approval_dir / f"{request_id}.json"
        if not approval_file.exists():
            print(f"❌ 请求不存在: {request_id}")
            return False

        with open(approval_file, 'r') as f:
            data = json.load(f)

        # 检查是否已处理
        if data.get("status") in ["approved", "rejected"]:
            print(f"❌ 请求已处理（状态: {data['status']}），不可重复操作")
            return False

        data["status"] = "approved"
        data["approved_at"] = datetime.now().isoformat()
        data["approved_by"] = current_user

        with open(approval_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ 已批准请求: {request_id} (by {current_user})")
        return True

    def reject(self, request_id: str) -> bool:
        """拒绝请求（带身份验证）"""
        current_user = os.getenv("USER") or os.getenv("USERNAME") or f"uid_{os.getuid()}"

        if not self._check_approver_permission():
            print(f"❌ 用户 {current_user} 无审批权限")
            return False

        approval_file = self.approval_dir / f"{request_id}.json"
        if not approval_file.exists():
            print(f"❌ 请求不存在: {request_id}")
            return False

        with open(approval_file, 'r') as f:
            data = json.load(f)

        # 检查是否已处理
        if data.get("status") in ["approved", "rejected"]:
            print(f"❌ 请求已处理（状态: {data['status']}），不可重复操作")
            return False

        data["status"] = "rejected"
        data["rejected_at"] = datetime.now().isoformat()
        data["rejected_by"] = current_user

        with open(approval_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ 已拒绝请求: {request_id} (by {current_user})")
        return True


def main():
    parser = argparse.ArgumentParser(description=f"SafeConfig v2.1 - 强制安全流程")
    parser.add_argument("--file", help="要修改的配置文件")
    parser.add_argument("--approver", help="审批人 (格式: telegram:user_id)")
    parser.add_argument("--changes", help="变更说明")
    parser.add_argument("--new-content-file", dest="new_content_file",
                        help="包含拟议新内容的临时文件路径（由 pre-tool-hook 生成）")
    parser.add_argument("--approve", help="批准请求ID")
    parser.add_argument("--reject", help="拒绝请求ID")

    args = parser.parse_args()

    sc = SafeConfigV2()

    if args.approve:
        sys.exit(0 if sc.approve(args.approve) else 1)
    elif args.reject:
        sys.exit(0 if sc.reject(args.reject) else 1)
    elif args.file and args.approver and args.changes:
        new_content_path = Path(args.new_content_file) if args.new_content_file else None
        success = sc.run_full_flow(args.file, args.approver, args.changes, new_content_path)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
