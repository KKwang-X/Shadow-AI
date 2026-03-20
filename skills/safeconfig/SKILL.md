---
name: safeconfig
description: AI Agent 配置守卫。通过 Claude Code PreToolUse Hook 在系统层面拦截关键配置文件的修改，强制执行备份+审批安全流程。拦截时自动捕获拟议内容并传递给 safeconfig-v2 完整流程。Use when: (1) Agent 尝试修改 openclaw.json 或其他关键配置, (2) 需要对配置变更进行审批和备份, (3) 需要防止 Agent 在无人监督下修改生产配置。
version: 1.2.0
author: KKwang-X
license: MIT
tags: [security, config-guard, pretooluse-hook, backup, approval, openclaw]
requirements:
  - python3 >= 3.8
  - openclaw
install: |
  git clone https://github.com/KKwang-X/Shadow-AI.git
  # 注册 Hook（在 ~/.claude/settings.json 中添加）:
  # "PreToolUse": [{"matcher": "Edit|Write|Bash", "hooks": [{"type": "command", "command": "python3 /path/to/safeconfig/pre-tool-hook.py", "timeout": 10}]}]
usage: |
  # 检查文件是否为关键配置
  python3 safeconfig.py --check ~/.openclaw/openclaw.json

  # 备份 + 审批流程
  python3 safeconfig.py --backup ~/.openclaw/openclaw.json --approver telegram:USER_ID --changes "变更说明"

  # 批准 / 拒绝请求
  python3 safeconfig.py --approve REQUEST_ID
  python3 safeconfig.py --reject REQUEST_ID
---

# SafeConfig v1 — AI Agent 配置守卫

🔒 **在 AI Agent 触碰关键配置文件之前，从系统层面拦截它。**

## 核心特性

- ✅ **PreToolUse Hook** — 拦截 Edit / Write / Bash 工具调用，在执行前检查目标文件
- ✅ **零绕过** — 在工具层面阻断，Agent 无法通过任何方式直接写入
- ✅ **内容捕获** — 拦截 Edit/Write 时提取拟议新内容，写入临时文件
- ✅ **一键交接** — 拦截消息自动附带 `--new-content-file` 参数，Agent 可直接执行 v2 流程
- ✅ **审计日志** — 所有 bypass 操作记录到 `~/.safeconfig/logs/`
- ✅ **紧急 bypass** — `SAFECONFIG_BYPASS=1` 环境变量，仅对当前 shell 会话生效

## 保护范围

| 类型 | 匹配规则 |
|------|---------|
| OpenClaw 配置 | `~/.openclaw/*.json` |
| Systemd 服务 | `/etc/systemd/system/*.service` |
| Nginx | `/etc/nginx/**` |
| SSH | `~/.ssh/config`, `/etc/ssh/sshd_config` |
| Claude 设置 | `.claude/settings*.json` |

## Hook 安装

在 `~/.claude/settings.json` 或项目 `.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write|Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/Shadow-AI/skills/safeconfig/pre-tool-hook.py",
        "timeout": 10
      }]
    }]
  }
}
```

## 快速开始

```bash
# 备份 + 审批（v1 流程）
python3 safeconfig.py \
  --backup ~/.openclaw/openclaw.json \
  --approver telegram:<审批人ID> \
  --changes "更新 API Key"

# 批准请求
python3 safeconfig.py --approve <request_id>
```

## 与 SafeConfig v2 的关系

Hook 拦截后，拦截消息中会给出 v2 完整流程的命令（含 `--new-content-file`）。v2 会接手执行：预审查→虚拟测试→应用→验证→回滚（如失败）。

推荐组合使用：Hook（拦截）+ v2（安全应用）。

## 文档

详见 [Shadow-AI README](../../README.zh.md)
