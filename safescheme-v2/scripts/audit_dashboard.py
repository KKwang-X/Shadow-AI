#!/usr/bin/env python3
"""
SafeConfig Audit Dashboard - 审计仪表板
可视化展示审计数据
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class AuditDashboard:
    """审计数据仪表板"""
    
    def __init__(self, log_dir: str = "~/.safeconfig/logs"):
        self.log_dir = Path(log_dir).expanduser()
    
    def load_entries(self, days: int = 30) -> list:
        """加载最近 N 天的审计条目"""
        entries = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for log_file in self.log_dir.glob("audit_*.jsonl"):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(data['timestamp'])
                        if entry_time >= cutoff:
                            entries.append(data)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        
        return sorted(entries, key=lambda x: x['timestamp'])
    
    def timeline_report(self, days: int = 7) -> str:
        """生成时间线报告"""
        entries = self.load_entries(days)
        
        # 按天统计
        daily_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failed': 0})
        
        for entry in entries:
            date = entry['timestamp'][:10]  # YYYY-MM-DD
            daily_stats[date]['total'] += 1
            if entry.get('status') == 'completed':
                daily_stats[date]['success'] += 1
            else:
                daily_stats[date]['failed'] += 1
        
        report = f"""
# SafeConfig 操作时间线 (最近 {days} 天)

| 日期 | 总操作 | 成功 | 失败 | 成功率 |
|------|--------|------|------|--------|
"""
        
        for date in sorted(daily_stats.keys(), reverse=True):
            stats = daily_stats[date]
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report += f"| {date} | {stats['total']} | {stats['success']} | {stats['failed']} | {success_rate:.1f}% |\n"
        
        return report
    
    def risk_analysis(self, days: int = 30) -> str:
        """风险分析报告"""
        entries = self.load_entries(days)
        
        # 统计失败和回滚
        failures = [e for e in entries if e.get('status') in ['failed', 'rolled_back']]
        
        fail_rate = len(failures)/len(entries)*100 if entries else 0
        
        report = f"""
# SafeConfig 风险分析 (最近 {days} 天)

## 总体风险

| 指标 | 数值 |
|------|------|
| 总操作 | {len(entries)} |
| 失败操作 | {len(failures)} |
| 失败率 | {fail_rate:.2f}% |

## 失败详情

"""
        
        if failures:
            report += "| 时间 | 操作 | 状态 | 变更 |\n"
            report += "|------|------|------|------|\n"
            for entry in failures[:10]:  # 最近 10 个失败
                report += f"| {entry['timestamp'][:16]} | {entry.get('action', 'unknown')} | {entry.get('status', 'unknown')} | {entry.get('changes', 'unknown')[:30]}... |\n"
        else:
            report += "✅ 最近 {days} 天无失败操作\n"
        
        return report
    
    def generate_html_dashboard(self, output_path: str = "~/.safeconfig/dashboard.html"):
        """生成 HTML 仪表板"""
        entries = self.load_entries(30)
        
        # 统计数据
        total = len(entries)
        success = len([e for e in entries if e.get('status') == 'completed'])
        failed = len([e for e in entries if e.get('status') == 'failed'])
        rolled_back = len([e for e in entries if e.get('status') == 'rolled_back'])
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SafeConfig 审计仪表板</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
        .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
        .success {{ color: #27ae60; }}
        .failed {{ color: #e74c3c; }}
        .warning {{ color: #f39c12; }}
        table {{ width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 SafeConfig 审计仪表板</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">总操作</div>
            </div>
            <div class="stat-card">
                <div class="stat-value success">{success}</div>
                <div class="stat-label">成功</div>
            </div>
            <div class="stat-card">
                <div class="stat-value failed">{failed}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat-card">
                <div class="stat-value warning">{rolled_back}</div>
                <div class="stat-label">已回滚</div>
            </div>
        </div>
        
        <h2>最近操作</h2>
        <table>
            <tr>
                <th>时间</th>
                <th>操作</th>
                <th>状态</th>
                <th>变更</th>
                <th>提交人</th>
            </tr>
"""
        
        # 添加最近 20 条记录
        for entry in entries[-20:]:
            status_class = "success" if entry.get('status') == 'completed' else "failed" if entry.get('status') == 'failed' else "warning"
            html += f"""
            <tr>
                <td>{entry['timestamp'][:16]}</td>
                <td>{entry.get('action', 'unknown')}</td>
                <td class="{status_class}">{entry.get('status', 'unknown')}</td>
                <td>{entry.get('changes', 'unknown')[:50]}...</td>
                <td>{entry.get('submitter', 'unknown')}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
</body>
</html>
"""
        
        output = Path(output_path).expanduser()
        with open(output, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML 仪表板已生成: {output}")
        return str(output)


def main():
    """命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SafeConfig 审计仪表板")
    parser.add_argument("--timeline", type=int, metavar="DAYS", help="生成时间线报告")
    parser.add_argument("--risk", type=int, metavar="DAYS", help="生成风险分析报告")
    parser.add_argument("--html", action="store_true", help="生成 HTML 仪表板")
    
    args = parser.parse_args()
    
    dashboard = AuditDashboard()
    
    if args.timeline:
        print(dashboard.timeline_report(args.timeline))
    elif args.risk:
        print(dashboard.risk_analysis(args.risk))
    elif args.html:
        dashboard.generate_html_dashboard()
    else:
        # 默认生成所有报告
        print(dashboard.timeline_report(7))
        print(dashboard.risk_analysis(30))
        dashboard.generate_html_dashboard()


if __name__ == "__main__":
    main()
