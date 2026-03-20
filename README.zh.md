<div align="center">

# 🛡️ Shadow-AI

**AI Agent 安全基础设施——让它们别把你的系统搞坏。**

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-6366f1?style=flat-square)](https://openclaw.dev)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-ff6b6b?style=flat-square)](CONTRIBUTING.md)

[English](README.md) · [中文](#) · [报告 Bug](https://github.com/KKwang-X/Shadow-AI/issues) · [功能建议](https://github.com/KKwang-X/Shadow-AI/discussions)

</div>

---

> *"我让 AI Agent 在生产服务器上跑起来了。它重写了配置，加了个根本不存在的参数，凌晨两点把服务搞挂了。没有备份。这个仓库就是这么来的。"*
> — KK

---

## 为什么会有这个项目

AI Agent（OpenClaw、Claude Code、Cursor 等）可以执行 shell 命令、编辑文件。但它们也会：

- **幻觉**出不存在的 CLI 参数（`--daemon`，你懂的）
- 在**没有备份、没有审批**的情况下直接写入关键配置
- 让你面对一个挂掉的服务，却没有任何回滚路径

Shadow-AI 在 Agent 和你的生产配置文件之间加入了一道**强制安全层**。Agent 无法绕过它——它在工具执行层面运作，在任何文件被触碰之前就已介入。

---

## 目录

- [架构](#架构)
- [快速开始](#快速开始)
- [功能模块](#功能模块)
  - [SafeConfig + PreToolUse Hook](#-safeconfig--pretooluse-hook)
  - [SafeConfig v2 — 9-Phase 完整流程](#-safeconfig-v2--9-phase-完整流程)
  - [Skill 安全审计器](#-skill-安全审计器)
  - [QQMail 邮件发送](#-qqmail-邮件发送)
- [仓库结构](#仓库结构)
- [踩坑实录](#踩坑实录)
- [参与贡献](#参与贡献)

---

## 架构

```
┌─────────────────────────────────────────────────────┐
│               AI Agent（Claude / OpenClaw）           │
└────────────────────────┬────────────────────────────┘
                         │ 调用 Edit / Write / Bash
                         ▼
┌─────────────────────────────────────────────────────┐
│         PreToolUse Hook（pre-tool-hook.py）           │  ← 在任何文件被触碰前触发
│                                                     │
│  是关键文件？──是──▶  exit 2  ──▶  操作被阻断         │
│       │                                             │
│      否                                             │
│       ▼                                             │
│    exit 0  ──▶  工具正常执行                         │
└─────────────────────────────────────────────────────┘
                         │ 操作被阻断时
                         ▼
┌─────────────────────────────────────────────────────┐
│          SafeConfig 安全流程（v1 或 v2）               │
│                                                     │
│  备份 → 审批 → 虚拟测试 → 应用 → 验证                 │
│                              └─ 验证失败时自动回滚     │
└─────────────────────────────────────────────────────┘
```

---

## 快速开始

**1. 安装 PreToolUse Hook**（一次性配置，约 60 秒）

在 `~/.claude/settings.json` 中添加：

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

> 项目自带 `.claude/settings.json`，已预配置好此 Hook。克隆即用。

**2. 让 Agent 尝试编辑关键配置（你的 Agent 现在受到保护了）**

```
╔══════════════════════════════════════════════════════════════╗
║           🚨 SafeConfig Hook — 操作已拦截                    ║
╚══════════════════════════════════════════════════════════════╝

工具:     Edit
目标文件: /root/.openclaw/openclaw.json

⛔ 禁止直接修改关键配置文件。

─── 方案 B：v2 完整 9-Phase 流程（推荐）────────────────────
  python3 safeconfig-v2.py \
    --file /root/.openclaw/openclaw.json \
    --approver telegram:<审批人ID> \
    --changes "本次变更说明" \
    --new-content-file /tmp/safeconfig_proposed_xyz.json
```

**3. 运行安全流程**

```bash
python3 safescheme-v2/scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:<审批人ID> \
  --changes "更新网关认证 Token" \
  --new-content-file /tmp/safeconfig_proposed_xyz.json
```

---

## 功能模块

### 🔒 SafeConfig + PreToolUse Hook

> `skills/safeconfig/` · 在系统层面拦截关键配置文件的修改

`pre-tool-hook.py` 注册为 Claude Code 的 `PreToolUse` Hook。每一次 `Edit`、`Write`、`Bash` 调用在执行前都会被检查。若目标为关键文件，操作立即**被阻断**，Agent 收到的消息中包含可直接复制执行的安全流程命令。

**默认保护的文件类型：**

| 匹配规则 | 示例 |
|---------|------|
| OpenClaw 配置 | `~/.openclaw/*.json` |
| Systemd 服务 | `/etc/systemd/system/*.service` |
| Nginx 配置 | `/etc/nginx/**` |
| SSH 配置 | `~/.ssh/config`、`/etc/ssh/sshd_config` |
| Claude 设置 | `.claude/settings*.json` |

**核心行为：**
- `Edit`/`Write` — 提取拟议新内容，保存到临时文件，在拦截消息中自动附带 `--new-content-file` 参数
- `Bash` — 扫描写入模式（`>`、`tee`、`sed -i`、`cp`、`mv`、`install`、`truncate`）
- `SAFECONFIG_BYPASS=1` — 紧急 bypass，所有绕过操作均记录到审计日志

```bash
# SafeConfig v1：备份 + 审批
python3 skills/safeconfig/safeconfig.py \
  --backup ~/.openclaw/openclaw.json \
  --approver telegram:<审批人ID> \
  --changes "更新 API Key"

# 批准请求
python3 skills/safeconfig/safeconfig.py --approve <request_id>
```

---

### 🔒 SafeConfig v2 — 9-Phase 完整流程

> `safescheme-v2/` · 高风险配置变更的结构化变更管理流程

完整、可审计的变更管理流水线。每个 Phase 必须通过才能进入下一个。Phase 8 失败时自动触发回滚。

```
Phase 1  预审查      验证当前配置的 Scheme 合规性（仅结构校验，不检查服务状态）
Phase 2  变更分析    变更影响分析
Phase 3  创建备份    生成带时间戳的备份至 ~/.config-backups/
Phase 4  生成审批    创建审批请求，通知审批人
Phase 5  等待审批    每 5 秒轮询一次（最多 30 分钟，Ctrl+C 可取消）
Phase 6  虚拟测试    将拟议内容写入隔离测试环境 → 验证 Scheme 合规性
Phase 7  执行变更    原子写入（来自 --new-content-file）或交互式确认
Phase 8  验证结果    重新验证已应用的配置 → 失败时通过 RollbackManager 自动回滚
Phase 9  审计归档    追加 JSONL 记录至 ~/.safeconfig/logs/audit_YYYYMM.jsonl
```

```bash
# 完整流程（Agent 模式——拟议内容由 Hook 捕获）
python3 safescheme-v2/scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:<审批人ID> \
  --changes "轮换网关认证 Token" \
  --new-content-file /tmp/safeconfig_proposed_xyz.json

# 在另一个终端批准 / 拒绝
python3 safescheme-v2/scripts/safeconfig-v2.py --approve <request_id>
python3 safescheme-v2/scripts/safeconfig-v2.py --reject <request_id>

# 手动回滚
python3 safescheme-v2/scripts/rollback_manager.py \
  --target ~/.openclaw/openclaw.json \
  --rollback ~/.config-backups/openclaw.json.20260320_143022.bak
```

---

### 🔍 Skill 安全审计器

> `skills/skill-security-auditor/` · 扫描已安装 Skill 中的安全漏洞

自动审计 OpenClaw 工作区中所有 Skill 的安全风险：

- 硬编码的密钥和凭证
- 危险的 shell 命令模式（不受限的 `eval`、`exec`、`os.system`）
- 系统边界处缺失的输入校验
- 过于宽泛的文件权限

```bash
# 人类可读报告
python3 skills/skill-security-auditor/scripts/auditor.py

# JSON 输出（适用于管道 / CI）
python3 skills/skill-security-auditor/scripts/auditor.py --json
```

---

### 📧 QQMail 邮件发送

> `skills/qqmail-sender/` · 基于 QQ 邮箱 SMTP 的邮件发送

国内网络最稳定的邮件方案，无需翻墙。SafeConfig 的通知系统用它来发送审批请求提醒。

```bash
# 环境变量配置
export QQMAIL_EMAIL="your-qq@qq.com"
export QQMAIL_AUTH_CODE="your-auth-code"  # 不是邮箱密码

python3 skills/qqmail-sender/qqmail.py "to@example.com" "主题" "正文"
```

**获取授权码：** QQ邮箱 → 设置 → 账户 → 开启SMTP服务 → 生成授权码

---

## 仓库结构

```
Shadow-AI/
├── .claude/
│   └── settings.json              # 已预配置 PreToolUse Hook
├── safescheme-v2/                 # 9-Phase 配置变更流程
│   ├── SKILL.md
│   ├── clawhub.json               # OpenClaw Skill 包元数据
│   └── scripts/
│       ├── safeconfig-v2.py       # 主流程控制器
│       ├── safescheme.py          # Scheme 验证器（16 项校验）
│       ├── rollback_manager.py    # 备份与回滚
│       ├── audit_logger.py        # 审计日志写入
│       ├── audit_dashboard.py     # HTML 报表生成
│       └── notification_system.py # Telegram / 邮件通知
└── skills/
    ├── safeconfig/                # PreToolUse Hook + v1 流程
    │   ├── safeconfig.py
    │   └── pre-tool-hook.py
    ├── skill-security-auditor/    # Skill 安全审计工具
    │   └── scripts/auditor.py
    └── qqmail-sender/             # QQ 邮箱 SMTP 发送
        └── qqmail.py
```

---

## 踩坑实录

这些工具源于真实事故。以下是发生过的问题，以便你知道需要防范什么。

### 幻觉 CLI 参数

```bash
# ❌ 模型自信地生成了这个——参数根本不存在
ExecStart=/path/to/openclaw gateway start --daemon
# 服务崩溃："unknown option '--daemon'"

# ✅ 先用 --help 验证
ExecStart=/path/to/openclaw gateway start
```

### 编辑前没有备份

```
Error: openclaw.json: unexpected token at line 12
# 没有备份。服务宕机。靠记忆手动恢复。
```
→ 现在：Phase 3 在每次变更前创建 `~/.config-backups/openclaw.json.{时间戳}.bak`

### 应用失败后没有回滚

```
Phase 8: Scheme validation failed after apply
⚠️  启动自动回滚...
✅ 已回滚到变更前状态
```
→ 现在：Phase 8 失败时自动调用 `RollbackManager.rollback()`

---

## 参与贡献

欢迎贡献，特别是：

- **新的关键路径规则** — 更多需要保护的配置文件类型
- **新的 Scheme 校验项** — 更多 OpenClaw 配置验证规则
- **平台集成** — Cursor、Windsurf、Cline Hook 支持
- **通知渠道** — Slack、钉钉、企业微信

大型 PR 请先开 Issue 讨论。

---

## 许可证

MIT — 详见 [LICENSE](LICENSE)

---

<div align="center">

从生产事故中炼出来的工具，by [KK](https://github.com/KKwang-X)<br>
<sub>OpenClaw 贡献者 · AI Agent 安全 · 无聊但可靠的基础设施倡导者</sub>

</div>
