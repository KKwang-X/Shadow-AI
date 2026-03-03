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

## 🎯 About Me

**OpenClaw Contributor** | AI Agent Practitioner | Production Safety Advocate

I'm KK, a business analyst at a major internet company in Beijing. Through extensive practice with AI agents, I've learned that **safety must come first when models have exec permissions**.

> 💡 "I've stepped on many landmines so you don't have to."

This repository documents my journey building AI agent systems, with special focus on **safe configuration management** and **production deployment best practices**.

---

## 🚀 Projects

### Shadow-AI (Original)
An AI engine integrating **GKD frontend controller** with **Large Language Models** for Android device automation via voice/text commands.

### SafeConfig ⭐ (Featured Skill)
A safety-first skill for OpenClaw/Codex that enforces strict security checks before modifying critical configurations.

**Why This Matters:**
When AI agents have `exec` permissions, a single hallucinated parameter can bring down production services. I learned this the hard way when `--daemon` (a non-existent parameter) crashed my OpenClaw gateway repeatedly.

**Key Features:**
- ✅ Validates parameter existence before modification
- ✅ Auto-backup with timestamps  
- ✅ Mandatory user confirmation
- ✅ Post-modification service verification
- ✅ Supports openclaw.json, systemd, nginx, ssh configs

**Quick Start:**
```bash
python3 skills/safeconfig/safeconfig.py --check ~/.openclaw/openclaw.json
python3 skills/safeconfig/safeconfig.py --backup /etc/systemd/system/myapp.service
```

### QQMail Sender 🇨🇳 (国内用户推荐)
**国内 OpenClaw 用户最便捷的邮件方案** - 无需 Gmail/Outlook，直接使用 QQ 邮箱，国内网络畅通无阻。

**Why This Matters:**
Gmail 在国内访问困难，Outlook 偶发连接问题。QQ 邮箱是国内最稳定的 SMTP 服务，人人有号，开箱即用。

**Key Features:**
- ✅ 国内网络畅通，无需翻墙
- ✅ QQ 号即邮箱，无需额外注册
- ✅ 支持系统告警、日报等自动化邮件
- ✅ 配置简单，授权码一键获取

**Quick Start:**
```bash
# 配置邮箱和授权码
export QQMAIL_EMAIL="your-qq@qq.com"
export QQMAIL_AUTH_CODE="your-auth-code"

# 发送邮件
python3 skills/qqmail-sender/qqmail.py "recipient@example.com" "主题" "正文"
```

**详细配置指南：** [skills/qqmail-sender/README.md](skills/qqmail-sender/README.md)

---

## 🛡️ Safety First Philosophy

### The Problem
Modern AI agents (OpenClaw, Claude Code, etc.) can execute shell commands. This is powerful but dangerous:
- Models can hallucinate non-existent parameters
- Config syntax errors can crash services
- No built-in safety guardrails

### The Solution
**SafeConfig** implements a 4-step safety workflow:

1. **Validate** — Check `--help` before using any parameter
2. **Backup** — Always backup before modification
3. **Confirm** — Show changes, get explicit user approval
4. **Verify** — Check service status after changes

### Real-World Impact
| Before SafeConfig | After SafeConfig |
|------------------------|----------------------|
| Service crashed 3 times in one night | Zero production incidents |
| `--daemon` parameter hallucination | All parameters validated |
| No rollback capability | Automatic timestamped backups |
| Silent failures | Explicit confirmation required |

---

## 📚 Lessons Learned (The Hard Way)

### Lesson 1: Never Trust Model-Generated Parameters
```bash
# ❌ Wrong: Model suggested this
ExecStart=/path/to/openclaw gateway start --daemon

# ✅ Correct: After checking --help
ExecStart=/path/to/openclaw gateway start
```

### Lesson 2: Always Backup Critical Configs
```bash
# Config Guardian auto-backup
~/.config-backups/openclaw.service.20250303_234439.bak
```

### Lesson 3: Verify After Every Change
```bash
sudo systemctl daemon-reload
sudo systemctl restart service
sudo systemctl status service --no-pager  # Must check!
```

---

## 🛠️ Skills Collection

| Skill | Description | Status |
|-------|-------------|--------|
| [SafeConfig](skills/safeconfig/) | Safe configuration management | ✅ Production Ready |
| [QQMail Sender](skills/qqmail-sender/) | QQ邮箱发送工具（国内推荐） | ✅ Ready |
| More coming... | | 🚧 In Development |

---

## 🤝 Contributing

Contributions welcome! Especially:
- Additional safety checks
- Support for more config formats
- Integration with other AI agent platforms

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ and lots of ☕ by <a href="https://github.com/KKwang-X">KK</a>
</p>
<p align="center">
  <sub>OpenClash Contributor • Safety Advocate • AI Agent Practitioner</sub>
</p>
