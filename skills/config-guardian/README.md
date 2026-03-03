---
name: config-guardian
description: Configuration modification safety guard skill. Enforces security checks before modifying critical config files (openclaw.json, systemd services, nginx, etc.): validate parameter existence, auto-backup, user confirmation. Use when: (1) modifying ~/.openclaw/openclaw.json, (2) modifying service configs in /etc/systemd/system/, (3) modifying nginx/ssh configs, (4) any config changes that may affect service operation.
---

# Config Guardian - Safe Configuration Management

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

## Usage Workflow

### Step 1: Check if Critical

```bash
python3 config-guardian.py --check <filepath>
```

### Step 2: Validate Parameters

**OpenClaw parameter validation:**
```bash
openclaw gateway start --help
# Confirm parameter exists in help text
```

**Systemd config validation:**
```bash
python3 config-guardian.py --validate-systemd <filepath>
systemd-analyze verify <filepath>
```

### Step 3: Create Backup

```bash
python3 config-guardian.py --backup <filepath>
```

Backup location: `~/.config-backups/<filename>.<timestamp>.bak`

### Step 4: Show Changes to User

Must display:
- File path being modified
- Before/after comparison
- Potential impact scope
- Rollback method

### Step 5: Get User Confirmation

Wait for explicit user response (e.g., "confirm", "execute", "ok") before proceeding.

### Step 6: Post-Validation

**Systemd services:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart <service>
sudo systemctl status <service> --no-pager
```

**OpenClaw:**
```bash
openclaw status
openclaw gateway status
```

## Safety Checklist

```
□ Does the parameter exist in current version? (check --help)
□ Has the original config been backed up?
□ Have changes been shown to the user?
□ Has explicit user confirmation been obtained?
□ Is the service status normal after modification?
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
cp ~/.config-backups/<filename>.<timestamp>.bak <original-path>

# Restart service
sudo systemctl restart <service>
```

## Installation

```bash
# Clone the script
curl -O https://raw.githubusercontent.com/KKwang-X/Shadow-AI/main/skills/config-guardian/config-guardian.py
chmod +x config-guardian.py

# Or copy to your PATH
sudo cp config-guardian.py /usr/local/bin/
```

## License

MIT
