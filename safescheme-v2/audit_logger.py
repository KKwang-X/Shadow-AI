#!/usr/bin/env python3
"""
SafeConfig Audit Logger - 审计日志系统
结构化记录所有配置变更操作
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class AuditEntry:
    """审计日志条目"""
    timestamp: str
    version: str
    request_id: str
    action: str  # "config_change", "approval", "rollback", "violation"
    filepath: str
    submitter: str
    approver: Optional[str]
    changes: str
    backup_path: Optional[str]
    status: str  # "completed", "failed", "rolled_back"
    phases: List[str]
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AuditLogger:
    """审计日志管理器"""
    
    def __init__(self, log_dir: str = "~/.safeconfig/logs"):
        self.log_dir = Path(log_dir).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log = self.log_dir / f"audit_{datetime.now().strftime('%Y%m')}.jsonl"
    
    def log(self, entry: AuditEntry):
        """记录审计日志"""
        # 追加到日志文件
        with open(self.current_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    
    def query(self, 
              start_date: Optional[str] = None,
              end_date: Optional[str] = None,
              action: Optional[str] = None,
              status: Optional[str] = None,
              limit: int = 100) -> List[AuditEntry]:
        """查询审计日志"""
        results = []
        
        # 读取所有日志文件
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        
                        # 过滤条件
                        if start_date and data['timestamp'] < start_date:
                            continue
                        if end_date and data['timestamp'] > end_date:
                            continue
                        if action and data['action'] != action:
                            continue
                        if status and data['status'] != status:
                            continue
                        
                        results.append(AuditEntry(**data))
                        
                        if len(results) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        
        return results
    
    def get_statistics(self) -> Dict:
        """获取审计统计"""
        stats = {
            "total_operations": 0,
            "successful": 0,
            "failed": 0,
            "rolled_back": 0,
            "by_action": {},
            "by_user": {}
        }
        
        log_files = list(self.log_dir.glob("audit_*.jsonl"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        stats["total_operations"] += 1
                        
                        # 状态统计
                        status = data.get('status', 'unknown')
                        if status == "completed":
                            stats["successful"] += 1
                        elif status == "failed":
                            stats["failed"] += 1
                        elif status == "rolled_back":
                            stats["rolled_back"] += 1
                        
                        # 按操作类型统计
                        action = data.get('action', 'unknown')
                        stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
                        
                        # 按用户统计
                        user = data.get('submitter', 'unknown')
                        stats["by_user"][user] = stats["by_user"].get(user, 0) + 1
                        
                    except json.JSONDecodeError:
                        continue
        
        return stats
    
    def generate_report(self, days: int = 30) -> str:
        """生成审计报告"""
        from_date = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.get_statistics()
        
        report = f"""
# SafeConfig 审计报告

生成时间: {datetime.now().isoformat()}
统计周期: 最近 {days} 天

## 操作统计

| 指标 | 数值 |
|------|------|
| 总操作数 | {stats['total_operations']} |
| 成功 | {stats['successful']} |
| 失败 | {stats['failed']} |
| 已回滚 | {stats['rolled_back']} |

## 按操作类型分布

| 操作类型 | 次数 |
|----------|------|
"""
        
        for action, count in sorted(stats['by_action'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {action} | {count} |\n"
        
        report += f"""
## 按用户分布

| 用户 | 操作次数 |
|------|----------|
"""
        
        for user, count in sorted(stats['by_user'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {user} | {count} |\n"
        
        report += "\n---\n*报告由 SafeConfig Audit Logger 生成*\n"
        
        return report


def main():
    """命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SafeConfig 审计日志工具")
    parser.add_argument("--report", action="store_true", help="生成审计报告")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--query", help="查询特定操作类型")
    parser.add_argument("--days", type=int, default=30, help="查询天数")
    
    args = parser.parse_args()
    
    logger = AuditLogger()
    
    if args.report:
        print(logger.generate_report(args.days))
    elif args.stats:
        stats = logger.get_statistics()
        print(json.dumps(stats, indent=2))
    elif args.query:
        entries = logger.query(action=args.query, limit=10)
        for entry in entries:
            print(f"[{entry.timestamp}] {entry.action}: {entry.changes} ({entry.status})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
