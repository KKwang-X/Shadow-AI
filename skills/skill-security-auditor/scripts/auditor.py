#!/usr/bin/env python3
"""
Skill Security Auditor - Skill 安全审计工具
检查已安装 skill 的安全风险
"""

import json
import os
from pathlib import Path
from typing import List, Dict


class SkillAuditor:
    """Skill 安全审计器"""
    
    def __init__(self, skills_dir: str = "~/.openclaw/workspace/skills"):
        self.skills_dir = Path(skills_dir).expanduser()
        self.issues = []
    
    def audit_all(self) -> List[Dict]:
        """审计所有 skill"""
        print("🔍 开始安全审计...")
        print("=" * 60)
        
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir() and not skill_path.name.startswith('.'):
                self._audit_skill(skill_path)
        
        return self.issues
    
    def _audit_skill(self, skill_path: Path):
        """审计单个 skill"""
        skill_name = skill_path.name
        print(f"\n📦 检查: {skill_name}")
        
        # 检查 1: 是否有 SKILL.md
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            self._add_issue(skill_name, "warning", "缺少 SKILL.md 元数据文件")
        
        # 检查 2: 是否有 README
        readme = skill_path / "README.md"
        if not readme.exists():
            self._add_issue(skill_name, "warning", "缺少 README.md 文档")
        
        # 检查 3: 检查 Python 文件中的危险操作
        for py_file in skill_path.rglob("*.py"):
            self._check_python_file(skill_name, py_file)
        
        # 检查 4: 检查 shell 脚本
        for sh_file in skill_path.rglob("*.sh"):
            self._check_shell_file(skill_name, sh_file)
    
    def _check_python_file(self, skill_name: str, file_path: Path):
        """检查 Python 文件安全问题"""
        try:
            content = file_path.read_text()
            
            # 危险操作检查
            dangerous_patterns = [
                ("os.system", "critical", "使用 os.system 执行系统命令"),
                ("subprocess.call", "warning", "使用 subprocess 执行命令"),
                ("eval(", "critical", "使用 eval 执行代码"),
                ("exec(", "critical", "使用 exec 执行代码"),
                ("__import__", "warning", "动态导入模块"),
                ("open(os.environ", "info", "访问环境变量"),
            ]
            
            for pattern, level, description in dangerous_patterns:
                if pattern in content:
                    self._add_issue(skill_name, level, f"{file_path.name}: {description}")
        
        except Exception as e:
            self._add_issue(skill_name, "error", f"无法读取 {file_path.name}: {e}")
    
    def _check_shell_file(self, skill_name: str, file_path: Path):
        """检查 shell 脚本安全问题"""
        try:
            content = file_path.read_text()
            
            dangerous_patterns = [
                ("rm -rf", "critical", "使用 rm -rf 强制删除"),
                ("curl | bash", "critical", "管道执行远程脚本"),
                ("wget | bash", "critical", "管道执行远程脚本"),
                ("sudo", "warning", "使用 sudo 提权"),
                ("chmod 777", "warning", "设置 777 权限"),
            ]
            
            for pattern, level, description in dangerous_patterns:
                if pattern in content:
                    self._add_issue(skill_name, level, f"{file_path.name}: {description}")
        
        except Exception as e:
            pass
    
    def _add_issue(self, skill: str, level: str, description: str):
        """添加问题记录"""
        issue = {
            "skill": skill,
            "level": level,
            "description": description
        }
        self.issues.append(issue)
        
        icon = {"critical": "🔴", "warning": "⚠️", "info": "ℹ️", "error": "❌"}.get(level, "⚪")
        print(f"  {icon} [{level.upper()}] {description}")
    
    def generate_report(self) -> str:
        """生成审计报告"""
        report = []
        report.append("\n" + "=" * 60)
        report.append("📊 安全审计报告")
        report.append("=" * 60)
        
        critical = len([i for i in self.issues if i["level"] == "critical"])
        warning = len([i for i in self.issues if i["level"] == "warning"])
        info = len([i for i in self.issues if i["level"] == "info"])
        
        report.append(f"\n总计问题: {len(self.issues)}")
        report.append(f"  🔴 严重: {critical}")
        report.append(f"  ⚠️  警告: {warning}")
        report.append(f"  ℹ️  信息: {info}")
        
        if critical > 0:
            report.append("\n🔴 严重问题（需要立即处理）:")
            for issue in self.issues:
                if issue["level"] == "critical":
                    report.append(f"  - [{issue['skill']}] {issue['description']}")
        
        return "\n".join(report)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Skill 安全审计工具")
    parser.add_argument("--skills-dir", help="Skill 目录路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    
    args = parser.parse_args()
    
    auditor = SkillAuditor(args.skills_dir) if args.skills_dir else SkillAuditor()
    issues = auditor.audit_all()
    
    if args.json:
        print(json.dumps(issues, indent=2, ensure_ascii=False))
    else:
        print(auditor.generate_report())
    
    # 返回码：有严重问题返回 1
    critical_count = len([i for i in issues if i["level"] == "critical"])
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    exit(main())
