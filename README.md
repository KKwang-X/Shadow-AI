# Shadow-AI

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Contributor-blue?style=flat-square" alt="OpenClaw Contributor">
  <img src="https://img.shields.io/badge/Python-3.8+-green?style=flat-square" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT License">
</p>

<p align="center">
  <b>English</b> | <a href="README.zh.md">中文</a>
</p>

---

A collection of production-hardened tools and skills for **safe AI agent operations** — born from real incidents where autonomous agents misconfigured production systems.

> 💡 *"I've stepped on many landmines so you don't have to."*
> — KK, OpenClaw Contributor

---

## 🛡️ The Problem This Solves

Modern AI agents (OpenClaw, Claude Code, etc.) can execute shell commands and edit files. This is powerful but dangerous:

- Models **hallucinate** non-existent CLI parameters
- Agents write to critical configs **without backup or approval**
- A single bad edit can take down a production service — with no rollback

**SafeConfig** and its ecosystem enforce a safety layer that agents cannot bypass.

---

## 🗂️ Repository Structure

```
Shadow-AI/
├── safedeploy.py              # One-command safe deployment
├── safescheme-v2/             # Full 9-phase config change workflow
└── skills/
    ├── safeconfig/            # Core config guard (v1) + PreToolUse Hook
    ├── qqmail-sender/         # QQ Mail SMTP sender
    └── skill-security-auditor/ # Automated skill security audit
```

---

## 🚀 Projects

### 🔒 SafeConfig v1 — Config Guard

Intercepts **any** attempt to edit critical config files before it happens.

**How it works:**

The `pre-tool-hook.py` registers as a Claude Code `PreToolUse` hook. Every time the agent calls `Edit`, `Write`, or `Bash`, the hook checks whether the target file is a critical config. If it is, the operation is **blocked at the system level** — the agent cannot proceed without going through the approval workflow.

```
Agent calls Edit ~/.openclaw/openclaw.json
        ↓
PreToolUse Hook fires (before execution)
        ↓
Critical config detected → exit 2 → Tool BLOCKED
        ↓
Agent must complete safeconfig flow first
```

**Quick Start:**
```bash
# Check if a file is a critical config
python3 skills/safeconfig/safeconfig.py --check ~/.openclaw/openclaw.json

# Backup + approval workflow
python3 skills/safeconfig/safeconfig.py \
  --backup ~/.openclaw/openclaw.json \
  --approver telegram:<your_id> \
  --changes "Update API key"

# Approve a pending request (run in a separate terminal)
python3 skills/safeconfig/safeconfig.py --approve <request_id>
```

**Hook installation** (one-time setup):

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

> The project `.claude/settings.json` ships with this hook pre-configured.

---

### 🔒 SafeConfig v2 — 9-Phase Workflow

A complete, structured change management process for high-stakes config changes.

```
Phase 1 → Pre-check (16 Scheme validations)
Phase 2 → Change analysis
Phase 3 → Triple backup
Phase 4 → Approval request
Phase 5 → Wait for approval (polls every 5s, 30-min timeout)
Phase 6 → Virtual environment test
Phase 7 → Apply change (interactive confirmation)
Phase 8 → Verify result
Phase 9 → Audit log
```

**Quick Start:**
```bash
python3 safescheme-v2/scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:<your_id> \
  --changes "Rotate gateway auth token"
```

---

### 🚀 SafeDeploy — One-Command Safe Deployment

Validates, fixes, backs up, and deploys in one shot.

```bash
# Check only (no changes)
python3 safedeploy.py check

# Check and auto-fix issues
python3 safedeploy.py fix

# Full deployment with approval workflow
python3 safedeploy.py deploy --approver telegram:<your_id> --changes "Update config"
```

**Auto-fixes:**

| Issue | Fix |
|-------|-----|
| Invalid flags (e.g. `--daemon`) | Removed automatically |
| JSON trailing commas | Cleaned up |
| Missing required fields | Default values injected |

📖 [Full SafeDeploy documentation](SAFEDEPLOY.md)

---

### 🔍 Skill Security Auditor

Scans all installed skills for security issues: hardcoded secrets, dangerous shell patterns, missing input validation, overly broad permissions.

```bash
python3 skills/skill-security-auditor/scripts/auditor.py
```

---

### 📧 QQMail Sender

SMTP email sender using QQ Mail — the most reliable option for users in mainland China (no VPN required).

```bash
export QQMAIL_EMAIL="your-qq@qq.com"
export QQMAIL_AUTH_CODE="your-auth-code"

python3 skills/qqmail-sender/qqmail.py "recipient@example.com" "Subject" "Body"
```

📖 [Configuration guide](skills/qqmail-sender/README.md)

---

## 🛠️ Skills Summary

| Skill | Purpose | Status |
|-------|---------|--------|
| [safeconfig](skills/safeconfig/) | Config guard + PreToolUse hook | ✅ Production |
| [safescheme-v2](safescheme-v2/) | 9-phase change workflow | ✅ Production |
| [skill-security-auditor](skills/skill-security-auditor/) | Skill security scanning | ✅ Production |
| [qqmail-sender](skills/qqmail-sender/) | QQ Mail SMTP sender | ✅ Production |

---

## 📚 Lessons Learned

### Lesson 1: Never trust model-generated parameters
```bash
# ❌ Model hallucinated this flag
ExecStart=/path/to/openclaw gateway start --daemon
# Result: service crash, "unknown option '--daemon'"

# ✅ Verified via --help
ExecStart=/path/to/openclaw gateway start
```

### Lesson 2: Always backup before any change
```
~/.config-backups/openclaw.service.20250303_234439.bak
```

### Lesson 3: Verify service status after every change
```bash
sudo systemctl daemon-reload && sudo systemctl restart openclaw
sudo systemctl status openclaw --no-pager
```

---

## 🤝 Contributing

Contributions welcome, especially:
- New safety checks and config format support
- Integration with other AI agent platforms (Cursor, Windsurf, etc.)
- Additional skill security audit rules

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  Built with ❤️ and hard-won experience by <a href="https://github.com/KKwang-X">KK</a><br>
  <sub>OpenClaw Contributor · Safety Advocate · AI Agent Practitioner</sub>
</p>
