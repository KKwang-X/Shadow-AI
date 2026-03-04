# Skill Security Auditor

🔍 **Skill 安全审计工具**

自动检查已安装 skill 的安全风险，识别潜在危险操作。

## 功能

- ✅ 检查危险 Python 操作（eval, exec, os.system 等）
- ✅ 检查危险 Shell 命令（rm -rf, curl | bash 等）
- ✅ 验证 SKILL.md 和 README 完整性
- ✅ 生成详细审计报告

## 使用

```bash
# 审计所有 skill
python3 scripts/auditor.py

# 输出 JSON 格式
python3 scripts/auditor.py --json

# 指定 skill 目录
python3 scripts/auditor.py --skills-dir /path/to/skills
```

## 风险等级

- 🔴 **Critical** - 严重风险，需要立即处理
- ⚠️ **Warning** - 警告，建议审查
- ℹ️ **Info** - 信息，了解即可
