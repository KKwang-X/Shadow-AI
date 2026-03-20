<div align="center">

# 🛡️ Shadow-AI

**Safety infrastructure for autonomous AI agents — stop them from breaking things.**

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-6366f1?style=flat-square)](https://openclaw.dev)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-ff6b6b?style=flat-square)](CONTRIBUTING.md)

[English](#) · [中文](README.zh.md) · [Report Bug](https://github.com/KKwang-X/Shadow-AI/issues) · [Request Feature](https://github.com/KKwang-X/Shadow-AI/discussions)

</div>

---

> *"I ran an AI agent on my production server. It rewrote the config, added a flag that doesn't exist, and took down the service at 2am. There was no backup. This repo is the result."*
> — KK

---

## Why This Exists

AI agents (OpenClaw, Claude Code, Cursor, etc.) can edit files and run shell commands. They also:

- **Hallucinate** CLI flags that don't exist (`--daemon`, anyone?)
- Write to critical configs **without backup**, **without approval**
- Leave you with a dead service and no rollback path

Shadow-AI adds a **mandatory safety layer** between agents and your production config files. Agents cannot bypass it — it operates at the tool execution level, before any file is touched.

---

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Skills](#skills)
  - [SafeConfig + PreToolUse Hook](#-safeconfig--pretooluse-hook)
  - [SafeConfig v2 — 9-Phase Workflow](#-safeconfig-v2--9-phase-workflow)
  - [Skill Security Auditor](#-skill-security-auditor)
  - [QQMail Sender](#-qqmail-sender)
- [Repo Structure](#repo-structure)
- [Lessons Learned](#lessons-learned)
- [Contributing](#contributing)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   AI Agent (Claude / OpenClaw)       │
└────────────────────────┬────────────────────────────┘
                         │ calls Edit / Write / Bash
                         ▼
┌─────────────────────────────────────────────────────┐
│              PreToolUse Hook (pre-tool-hook.py)      │  ← runs BEFORE any file is touched
│                                                     │
│  Critical file?  ──YES──▶  exit 2  ──▶  BLOCKED     │
│       │                                             │
│      NO                                             │
│       ▼                                             │
│    exit 0  ──▶  Tool executes normally              │
└─────────────────────────────────────────────────────┘
                         │ if blocked
                         ▼
┌─────────────────────────────────────────────────────┐
│          SafeConfig Flow (v1 or v2)                  │
│                                                     │
│  Backup → Approval → Virtual Test → Apply → Verify  │
│                                    └─ auto-rollback on failure
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

**1. Install the PreToolUse Hook** (one-time, takes 60 seconds)

Add to `~/.claude/settings.json`:

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

> The project ships with `.claude/settings.json` pre-configured. Clone and go.

**2. Try to edit a critical config (your agent is now protected)**

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

**3. Run the safe flow**

```bash
python3 safescheme-v2/scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:<your_id> \
  --changes "Update gateway token" \
  --new-content-file /tmp/safeconfig_proposed_xyz.json
```

---

## Skills

### 🔒 SafeConfig + PreToolUse Hook

> `skills/safeconfig/` · Intercepts critical config edits at the system level

The `pre-tool-hook.py` registers as a Claude Code `PreToolUse` hook. Every `Edit`, `Write`, or `Bash` call is inspected before execution. If the target is a critical file, the operation is **blocked** and the agent is given the exact command to run the safe flow instead.

**Protected by default:**

| Pattern | Examples |
|---------|----------|
| OpenClaw config | `~/.openclaw/*.json` |
| Systemd units | `/etc/systemd/system/*.service` |
| Nginx config | `/etc/nginx/**` |
| SSH config | `~/.ssh/config`, `/etc/ssh/sshd_config` |
| Claude settings | `.claude/settings*.json` |

**Key behaviors:**
- `Edit`/`Write` — captures the proposed new content, saves to a temp file, and includes `--new-content-file` in the block message so the agent can hand it directly to the v2 flow
- `Bash` — scans for write patterns (`>`, `tee`, `sed -i`, `cp`, `mv`, `install`, `truncate`)
- `SAFECONFIG_BYPASS=1` — emergency bypass, all bypasses logged to audit

```bash
# Safeconfig v1: backup + approval
python3 skills/safeconfig/safeconfig.py \
  --backup ~/.openclaw/openclaw.json \
  --approver telegram:<your_id> \
  --changes "Update API key"

# Approve a request
python3 skills/safeconfig/safeconfig.py --approve <request_id>
```

---

### 🔒 SafeConfig v2 — 9-Phase Workflow

> `safescheme-v2/` · Structured change management for high-stakes config changes

A complete, auditable change management pipeline. Each phase must pass before the next begins. Phase 8 failure triggers automatic rollback.

```
Phase 1  Pre-check      Validate current config against Scheme (structure only, not service status)
Phase 2  Analysis       Change impact analysis
Phase 3  Backup         Create timestamped backup to ~/.config-backups/
Phase 4  Approval       Generate approval request, notify approver
Phase 5  Wait           Poll for approval every 5s (30-min timeout, Ctrl+C to cancel)
Phase 6  Virtual Test   Write proposed content to isolated test env → validate Scheme
Phase 7  Apply          Atomic write from --new-content-file (or interactive for humans)
Phase 8  Verify         Re-validate applied config → auto-rollback via RollbackManager if failed
Phase 9  Audit Log      Append JSONL entry to ~/.safeconfig/logs/audit_YYYYMM.jsonl
```

```bash
# Full flow (agent mode — proposed content captured by hook)
python3 safescheme-v2/scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:<your_id> \
  --changes "Rotate gateway auth token" \
  --new-content-file /tmp/safeconfig_proposed_xyz.json

# Approve / reject from another terminal
python3 safescheme-v2/scripts/safeconfig-v2.py --approve <request_id>
python3 safescheme-v2/scripts/safeconfig-v2.py --reject <request_id>

# Manual rollback
python3 safescheme-v2/scripts/rollback_manager.py \
  --target ~/.openclaw/openclaw.json \
  --rollback ~/.config-backups/openclaw.json.20260320_143022.bak
```

---

### 🔍 Skill Security Auditor

> `skills/skill-security-auditor/` · Scan installed skills for vulnerabilities

Automatically audits all skills in your OpenClaw workspace for:

- Hardcoded secrets and credentials
- Dangerous shell patterns (unrestricted `eval`, `exec`, `os.system`)
- Missing input validation at system boundaries
- Overly broad file permissions

```bash
# Human-readable report
python3 skills/skill-security-auditor/scripts/auditor.py

# JSON output (for piping / CI)
python3 skills/skill-security-auditor/scripts/auditor.py --json
```

---

### 📧 QQMail Sender

> `skills/qqmail-sender/` · SMTP email via QQ Mail

The most reliable email option for users in mainland China (no VPN required). Used by SafeConfig's notification system for approval request alerts.

```bash
# Environment variable config
export QQMAIL_EMAIL="your-qq@qq.com"
export QQMAIL_AUTH_CODE="your-auth-code"  # NOT your password

python3 skills/qqmail-sender/qqmail.py "to@example.com" "Subject" "Body"
```

**Getting the auth code:** QQ Mail → Settings → Account → Enable SMTP → Generate Auth Code

---

## Repo Structure

```
Shadow-AI/
├── .claude/
│   └── settings.json              # PreToolUse hook pre-configured
├── safescheme-v2/                 # 9-Phase config change workflow
│   ├── SKILL.md
│   ├── clawhub.json               # OpenClaw skill package metadata
│   └── scripts/
│       ├── safeconfig-v2.py       # Main flow controller
│       ├── safescheme.py          # Scheme validator (16 checks)
│       ├── rollback_manager.py    # Backup & rollback
│       ├── audit_logger.py        # Audit log writer
│       ├── audit_dashboard.py     # HTML report generator
│       └── notification_system.py # Telegram / email alerts
└── skills/
    ├── safeconfig/                # PreToolUse hook + v1 flow
    │   ├── safeconfig.py
    │   └── pre-tool-hook.py
    ├── skill-security-auditor/    # Security audit tool
    │   └── scripts/auditor.py
    └── qqmail-sender/             # QQ Mail SMTP sender
        └── qqmail.py
```

---

## Lessons Learned

These tools were built from real incidents. Here's what went wrong so you know what to guard against.

### Hallucinated CLI flags

```bash
# ❌ Model confidently generated this — flag doesn't exist
ExecStart=/path/to/openclaw gateway start --daemon
# Service crashed: "unknown option '--daemon'"

# ✅ Verified via --help first
ExecStart=/path/to/openclaw gateway start
```

### No backup before edit

```
Error: openclaw.json: unexpected token at line 12
# No backup. Service down. Manual recovery from memory.
```
→ Now: Phase 3 creates `~/.config-backups/openclaw.json.{timestamp}.bak` before every change.

### No rollback after bad apply

```
Phase 8: Scheme validation failed after apply
⚠️  启动自动回滚...
✅ 已回滚到变更前状态
```
→ Now: Phase 8 auto-triggers `RollbackManager.rollback()` on failure.

---

## Contributing

Contributions welcome, especially:

- **New critical path patterns** — additional config files that should be protected
- **New Scheme checks** — more validation rules for OpenClaw config
- **Platform integrations** — Cursor, Windsurf, Cline hooks
- **Notification channels** — Slack, DingTalk, WeCom

Please open an issue before large PRs.

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Built from production incidents by [KK](https://github.com/KKwang-X)<br>
<sub>OpenClaw Contributor · AI Agent Safety · Advocate for boring, reliable infrastructure</sub>

</div>
