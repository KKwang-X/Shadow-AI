#!/usr/bin/env python3
"""
SafeConfig Rollback Manager - 回滚机制
自动和手动回滚配置变更
"""

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, backup_dir: str = "~/.config-backups"):
        self.backup_dir = Path(backup_dir).expanduser()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def list_backups(self, filename: Optional[str] = None) -> List[Dict]:
        """列出所有备份"""
        backups = []
        
        pattern = f"{filename}.*.bak" if filename else "*.bak"
        for backup_file in sorted(self.backup_dir.glob(pattern), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "path": str(backup_file),
                "filename": backup_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return backups
    
    def rollback(self, target_file: str, backup_file: Optional[str] = None) -> bool:
        """回滚到指定备份"""
        target = Path(target_file).expanduser()
        
        # 如果没有指定备份文件，使用最新的
        if not backup_file:
            backups = self.list_backups(target.name)
            if not backups:
                print(f"❌ 没有找到 {target.name} 的备份")
                return False
            backup_file = backups[0]["path"]
        
        backup = Path(backup_file)
        if not backup.exists():
            print(f"❌ 备份文件不存在: {backup}")
            return False
        
        # 验证备份文件
        try:
            with open(backup, 'r') as f:
                json.load(f)  # 验证是有效的 JSON
        except json.JSONDecodeError:
            print(f"❌ 备份文件损坏: {backup}")
            return False
        
        # 创建当前状态的备份（防止回滚失败）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = self.backup_dir / f"{target.name}.{timestamp}.pre-rollback.bak"
        shutil.copy2(target, current_backup)
        print(f"✅ 当前状态已备份: {current_backup}")
        
        # 执行回滚
        try:
            shutil.copy2(backup, target)
            print(f"✅ 已回滚到: {backup}")
            
            # 验证回滚后的文件
            with open(target, 'r') as f:
                json.load(f)
            print(f"✅ 回滚后文件验证通过")
            
            return True
            
        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            # 尝试恢复
            try:
                shutil.copy2(current_backup, target)
                print(f"⚠️  已恢复到回滚前状态")
            except:
                pass
            return False
    
    def auto_rollback_on_failure(self, target_file: str, backup_file: str, test_func=None) -> bool:
        """测试失败时自动回滚"""
        print("🔍 执行变更后测试...")
        
        # 如果没有提供测试函数，使用默认测试
        if test_func is None:
            test_func = lambda: self._default_test(target_file)
        
        if test_func():
            print("✅ 测试通过，无需回滚")
            return True
        
        print("❌ 测试失败，启动自动回滚...")
        return self.rollback(target_file, backup_file)
    
    def _default_test(self, target_file: str) -> bool:
        """默认测试：验证 JSON 语法"""
        try:
            with open(target_file, 'r') as f:
                json.load(f)
            return True
        except:
            return False
    
    def interactive_rollback(self, target_file: str):
        """交互式回滚"""
        print(f"🔙 交互式回滚: {target_file}")
        print("-" * 60)
        
        # 列出备份
        backups = self.list_backups(Path(target_file).name)
        
        if not backups:
            print("❌ 没有找到备份")
            return False
        
        print("可用备份:")
        for i, backup in enumerate(backups[:10], 1):
            print(f"{i}. {backup['filename']} ({backup['created']})")
        
        print("\n选项:")
        print("  1-10: 选择备份回滚")
        print("  0: 取消")
        print("  c: 清理旧备份")
        
        choice = input("\n选择: ").strip()
        
        if choice == "0":
            print("已取消")
            return False
        elif choice == "c":
            keep = input("保留最近几个备份? ").strip()
            self.cleanup_old_backups(int(keep) if keep.isdigit() else 10)
            return True
        elif choice.isdigit() and 1 <= int(choice) <= len(backups):
            selected = backups[int(choice) - 1]
            confirm = input(f"确认回滚到 {selected['filename']}? (yes/no): ").strip().lower()
            if confirm == "yes":
                return self.rollback(target_file, selected['path'])
        
        print("无效选择")
        return False
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """清理旧备份"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            print(f"✅ 备份数量 ({len(backups)}) 在限制内，无需清理")
            return
        
        to_delete = backups[keep_count:]
        for backup in to_delete:
            try:
                Path(backup["path"]).unlink()
                print(f"🗑️  已删除旧备份: {backup['filename']}")
            except Exception as e:
                print(f"⚠️  删除失败 {backup['filename']}: {e}")
        
        print(f"✅ 清理完成，保留 {keep_count} 个最新备份")


def main():
    """命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SafeConfig 回滚管理器")
    parser.add_argument("--list", help="列出备份 (指定文件名)")
    parser.add_argument("--rollback", help="回滚到指定备份")
    parser.add_argument("--target", required=True, help="目标配置文件")
    parser.add_argument("--cleanup", type=int, metavar="N", help="清理旧备份，保留 N 个")
    
    args = parser.parse_args()
    
    manager = RollbackManager()
    
    if args.list is not None:
        backups = manager.list_backups(args.list or None)
        print(f"找到 {len(backups)} 个备份:")
        for i, backup in enumerate(backups[:10], 1):
            print(f"{i}. {backup['filename']} ({backup['size']} bytes, {backup['created']})")
    
    elif args.rollback:
        success = manager.rollback(args.target, args.rollback)
        sys.exit(0 if success else 1)
    
    elif args.cleanup:
        manager.cleanup_old_backups(args.cleanup)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    import sys
    main()
