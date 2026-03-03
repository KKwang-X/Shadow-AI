---
name: safeconfig
description: Safe configuration management skill for AI agents. Enforces security checks before modifying critical config files (openclaw.json, systemd services, nginx, etc.): validate parameter existence, auto-backup, user confirmation. Use when: (1) modifying ~/.openclaw/openclaw.json, (2) modifying service configs in /etc/systemd/system/, (3) modifying nginx/ssh configs, (4) any config changes that may affect service operation.
---

# SafeConfig - Safe Configuration Management

> <strong>⚠️ Why This Skill Exists</strong><br>
> When AI agents have `exec` permissions, a single hallucinated parameter can bring down production services. This skill was born from real pain — I once crashed my OpenClaw gateway 3 times in one night because the model suggested `--daemon`, a parameter that doesn't exist.

## Core Principles

**All critical configuration modifications must follow this workflow:**

1. **Validate First** — Confirm parameter exists using `--help` or documentation
2. **Auto Backup** — Create timestamped backup before modification  
3. **User Confirmation** — Show changes to user and get explicit approval
4. **Post-Validation** — Verify service status after modification

## Critical Config Files

| File Path | Type | Risk Level |
|---------|------|---------|
| `~/.openclaw/openclaw.json` | OpenClaw Config | 🔴 High |
| `/etc/systemd/system/*.service` | Systemd Service | 🔴 High |
| `/etc/nginx/nginx.conf` | Nginx Config | 🟡 Medium |
| `~/.ssh/config` | SSH Config | 🟡 Medium |

## Real-World Lessons Learned

### Lesson 1: Never Trust Model-Generated Parameters
```bash
# ❌ WRONG: Model suggested this parameter
ExecStart=/home/admin/.npm-global/bin/openclaw gateway start --daemon
# Result: Service crashed with "unknown option '--daemon'"

# ✅ CORRECT: After checking --help
ExecStart=/home/admin/.npm-global/bin/openclaw gateway start
# Result: Service started successfully
```

### Lesson 2: Always Backup Before Changes
Without backups, one wrong edit can leave you scrambling. SafeConfig automatically creates timestamped backups:
```
~/.config-backups/openclaw.service.20250303_234439.bak
```

### Lesson 3: Verify After Every Change
```bash
sudo systemctl daemon-reload
sudo systemctl restart openclaw
sudo systemctl status openclaw --no-pager  # MUST CHECK!
```

## Installation

```bash
# Clone the repository
git clone https://github.com/KKwang-X/Shadow-AI.git
cd Shadow-AI

# Make executable
chmod +x skills/safeconfig/safeconfig.py

# Optional: Add to PATH
sudo cp skills/safeconfig/safeconfig.py /usr/local/bin/
```

## Usage

### Check if File is Critical
```bash
python3 safeconfig.py --check ~/.openclaw/openclaw.json
# Output: Critical config: Yes
```

### Backup Config File
```bash
python3 safeconfig.py --backup /etc/systemd/system/myapp.service
# Output: ✅ Backup created: ~/.config-backups/myapp.service.20250303_234439.bak
```

### Validate Systemd Config
```bash
python3 safeconfig.py --validate-systemd /etc/systemd/system/myapp.service
# Output: ✅ systemd config validated
```

## Safety Checklist

Before modifying any critical config:

```
□ Does the parameter exist in current version? (check --help)
□ Has the original config been backed up?
□ Have changes been shown to the user?
□ Has explicit user confirmation been obtained?
□ Is the service status normal after modification?
```

## Integration with OpenClaw/Codex

Add this to your agent's instructions:

```markdown
## Config Safety Rules

When modifying critical configuration files:
1. Run `safeconfig.py --check <filepath>` to identify critical configs
2. Run `safeconfig.py --backup <filepath>` before any changes
3. For systemd: Run `safeconfig.py --validate-systemd <file>`
4. Show user the exact changes before applying
5. Get explicit confirmation ("confirm", "execute", "ok")
6. Verify service status after changes
```

## Common Error Prevention

| Error Scenario | Prevention |
|---------|---------|
| Using non-existent parameters | Run `--help` to verify before modification |
| Config syntax errors | Use `systemd-analyze verify` to check |
| Service fails to start | Backup before modification for rollback |
| Permission issues | Check file permissions beforehand, use sudo when needed |

## Rollback Method

If issues occur after modification:

```bash
# Restore from backup
cp ~/.config-backups/myapp.service.20250303_234439.bak /etc/systemd/system/myapp.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart myapp
```

## Why This Matters for AI Agents

AI agents with `exec` permissions can:
- Execute arbitrary shell commands
- Modify system configurations
- Start/stop services

**Without guardrails, this is dangerous.** Models can:
- Hallucinate non-existent parameters
- Generate syntactically incorrect configs
- Apply changes without verification

**SafeConfig adds the safety layer that should be built-in.**

## License

MIT License - See [LICENSE](../../LICENSE) for details.

---

<p align="center">
  Built with ❤️ and hard-learned lessons by <a href="https://github.com/KKwang-X">KK</a>
</p>

