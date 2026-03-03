---
name: safeconfig
description: Configuration modification safety guard skill. Enforces security checks before modifying critical config files (openclaw.json, systemd services, nginx, etc.): validate parameter existence, auto-backup, user confirmation, optional approver workflow. Use when: (1) modifying ~/.openclaw/openclaw.json, (2) modifying service configs in /etc/systemd/system/, (3) modifying nginx/ssh configs, (4) any config changes that may affect service operation, (5) production environments requiring approver confirmation.
---

# SafeConfig - Safe Configuration Management

> **⚠️ Why This Skill Exists**
> When AI agents have `exec` permissions, a single hallucinated parameter can bring down production services. This skill was born from real pain — I once crashed my OpenClaw gateway 3 times in one night because the model suggested `--daemon`, a parameter that doesn't exist.

## Core Principles

**All critical configuration modifications must follow this workflow:**

1. **Validate First** — Confirm parameter exists using `--help` or documentation
2. **Auto Backup** — Create timestamped backup before modification  
3. **User Confirmation** — Show changes to user and get explicit approval
4. **Approver Confirmation** (Optional) — For production environments, require a second person to approve
5. **Post-Validation** — Verify service status after modification

## 🔐 Approver Workflow (New Feature)

For production environments or sensitive operations, SafeConfig supports an **optional approver workflow**:

### Why Use Approver?

| Scenario | Without Approver | With Approver |
|----------|-----------------|---------------|
| Single user | Risk of accidental changes | Self-approval with audit trail |
| Team environment | No oversight | Second pair of eyes |
| Production systems | Direct modification | Controlled release |
| Compliance requirements | No audit trail | Full audit log |

### How It Works

```
User requests change → Approver notified → Approver approves → Change executed
```

### Usage

**Request change with approver:**
```bash
# Telegram approver
python3 safeconfig.py --backup /etc/nginx/nginx.conf \
  --approver telegram:admin \
  --changes "Update SSL certificate"

# Email approver
python3 safeconfig.py --backup /etc/systemd/system/myapp.service \
  --approver email:admin@company.com \
  --changes "Update exec command"
```

**Approver actions:**
```bash
# Approve request
python3 safeconfig.py --approve req_20250304_123456_abc123

# Reject request
python3 safeconfig.py --reject req_20250304_123456_abc123
```

### Workflow Details

1. **Request Phase**
   - User runs command with `--approver`
   - SafeConfig generates unique request ID
   - Request saved to `~/.safeconfig/approvals/`
   - Notification sent to approver (Telegram/Email)

2. **Approval Phase**
   - Approver receives notification with change details
   - Approver replies "approve" or "reject"
   - Or manually edits approval file status

3. **Execution Phase**
   - SafeConfig polls for approval (max 30 min)
   - On approval: executes backup/modification
   - On rejection: cancels operation
   - On timeout: cancels operation

### Approval File Format

```json
{
  "request_id": "req_20250304_123456_abc123",
  "channel": "telegram",
  "recipient": "admin",
  "message": "🔐 SafeConfig 审批请求...",
  "status": "pending",
  "created_at": "2025-03-04T12:34:56",
  "expires_at": "2025-03-04T13:04:56"
}
```

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

### Backup with Approver (Production)
```bash
python3 safeconfig.py --backup /etc/nginx/nginx.conf \
  --approver telegram:ops_team \
  --changes "Update SSL certificate for new domain"
```

### Validate Systemd Config
```bash
python3 safeconfig.py --validate-systemd /etc/systemd/system/myapp.service
# Output: ✅ systemd config validated
```

### Approve/Reject Requests
```bash
# List pending requests
ls ~/.safeconfig/approvals/

# Approve
python3 safeconfig.py --approve req_20250304_123456_abc123

# Reject
python3 safeconfig.py --reject req_20250304_123456_abc123
```

## Safety Checklist

```
□ Does the parameter exist in current version? (check --help)
□ Has the original config been backed up?
□ Have changes been shown to the user?
□ Has explicit user confirmation been obtained?
□ (Optional) Has approver confirmed the change?
□ Is the service status normal after modification?
```

## Integration with OpenClaw/Codex

Add this to your agent's instructions:

```markdown
## Config Safety Rules

When modifying critical configuration files:
1. Run `safeconfig.py --check <filepath>` to identify critical configs
2. Run `safeconfig.py --backup <filepath>` before any changes
3. For production: Add `--approver telegram:admin` or `--approver email:admin@company.com`
4. For systemd: Run `safeconfig.py --validate-systemd <file>`
5. Show user the exact changes before applying
6. Get explicit confirmation ("confirm", "execute", "ok")
7. Verify service status after changes
```

## Common Error Prevention

| Error Scenario | Prevention |
|---------|---------|
| Using non-existent parameters | Run `--help` to verify before modification |
| Config syntax errors | Use `systemd-analyze verify` to check |
| Service fails to start | Backup before modification for rollback |
| Permission issues | Check file permissions beforehand, use sudo when needed |
| Unauthorized changes | Use `--approver` for production environments |

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
- Make changes without oversight

**SafeConfig adds the safety layer that should be built-in.**

## License

MIT License - See [LICENSE](../../LICENSE) for details.

---

<p align="center">
  Built with ❤️ and hard-learned lessons by <a href="https://github.com/KKwang-X">KK</a>
</p>