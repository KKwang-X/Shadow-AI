<div align="center">

# 🔐 SafeConfig v2.1

<p align="center">
  <b>不可绕过的强制配置安全管理流程</b>
</p>

<p align="center">
  <a href="https://github.com/KKwang-X/Shadow-AI/releases"><img src="https://img.shields.io/github/v/release/KKwang-X/Shadow-AI?style=flat-square&color=blue" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/KKwang-X/Shadow-AI?style=flat-square&color=green" alt="License"></a>
  <a href="https://openclaw.ai"><img src="https://img.shields.io/badge/OpenClaw-Compatible-orange?style=flat-square" alt="OpenClaw"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat-square" alt="Tests"></a>
</p>

<p align="center">
  <a href="README.zh.md"><img src="https://img.shields.io/badge/中文-文档-red?style=flat-square" alt="中文"></a>
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#documentation">Docs</a> •
  <a href="#contributing">Contributing</a>
</p>

</div>

---

## 🎯 What is SafeConfig?

SafeConfig is an **unbypassable forced security workflow** for configuration management. It ensures every configuration change goes through a rigorous 9-phase process before reaching production.

```
┌─────────────────────────────────────────────────────────────┐
│  Before SafeConfig          After SafeConfig                │
│  ─────────────────          ────────────────                │
│                                                             │
│  vim config.json    →    16 Scheme Checks ✅               │
│  systemctl restart  →    Virtual Environment Test ✅       │
│  Hope it works      →    Approval + Audit Trail ✅         │
│                                                             │
│  🔴 Risk: High           🟢 Risk: Minimal                  │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔒 Security First
- **9-Phase Forced Workflow** - No step can be skipped
- **16-Point Scheme Validation** - Based on OpenClaw specs
- **Virtual Environment Testing** - Test before production
- **Double Approval** - Auto-checks + Human approval

</td>
<td width="50%">

### 📊 Full Visibility
- **Complete Audit Trail** - Every action logged
- **HTML Dashboard** - Visual reports
- **Risk Analysis** - Identify issues early
- **Timeline Reports** - Track changes over time

</td>
</tr>
<tr>
<td>

### 🔄 Safety Net
- **One-Click Rollback** - Auto/manual/interactive
- **Triple Backup Strategy** - L1/L2/L3 backups
- **Failure Detection** - Auto-rollback on issues
- **Recovery Testing** - Verified restore process

</td>
<td>

### 🚀 Developer Experience
- **Simple CLI** - Easy to use
- **Clear Output** - Know what's happening
- **Fast Feedback** - Quick validation
- **Git Integration** - Version controlled configs

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/KKwang-X/Shadow-AI.git

# Install to OpenClaw skills
cp -r Shadow-AI/safescheme-v2 ~/.openclaw/workspace/skills/
cd ~/.openclaw/workspace/skills/safescheme-v2
```

### Basic Usage

```bash
# Run full SafeConfig workflow
python3 scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:8028839180 \
  --changes "Update API configuration"

# Approve pending request
python3 scripts/safeconfig-v2.py --approve <request-id>
```

### One-Liner Install

```bash
curl -sSL https://raw.githubusercontent.com/KKwang-X/Shadow-AI/main/install.sh | bash
```

---

## 📋 The 9-Phase Workflow

<details open>
<summary><b>Click to see detailed workflow</b></summary>

| Phase | Name | Description | Duration |
|-------|------|-------------|----------|
| 0 | **Intent Declaration** | Declare operation intent | < 1s |
| 1 | **Pre-Check** | 16-point scheme validation | ~2s |
| 2 | **Change Analysis** | Detailed impact analysis | ~1s |
| 3 | **Backup Creation** | L1/L2/L3 backup strategy | ~1s |
| 4 | **Approval Request** | Generate approval ticket | < 1s |
| 5 | **Await Approval** | Human approval required | Variable |
| 6 | **Virtual Testing** | Isolated environment test | ~10s |
| 7 | **Apply Changes** | Production deployment | ~2s |
| 8 | **Verification** | Multi-dimension validation | ~3s |
| 9 | **Audit Log** | Complete record archiving | < 1s |

</details>

---

## 🛡️ 16-Point Scheme Validation

<details>
<summary><b>View all validation checks</b></summary>

### File & Syntax
- ✅ **File Existence** - Config file must exist
- ✅ **JSON Syntax** - Must be valid JSON
- ✅ **Schema Structure** - Required fields present
- ✅ **Type Checking** - Correct data types

### Configuration
- ✅ **Required Fields** - botToken, auth tokens
- ✅ **Value Ranges** - Valid enum values
- ✅ **Dependencies** - Enabled features configured
- ✅ **Security** - No placeholder API keys

### System Health
- ✅ **Service Status** - OpenClaw running
- ✅ **Port Health** - Gateway port listening
- ✅ **Disk Space** - < 80% usage
- ✅ **Memory Status** - Sufficient memory

### Compatibility
- ✅ **Version Match** - Config compatible
- ✅ **Log Check** - No critical errors
- ✅ **Resource Check** - System resources OK
- ✅ **Network Check** - Connectivity verified

</details>

---

## 📊 Dashboard & Reporting

### Generate HTML Dashboard

```bash
python3 scripts/audit_dashboard.py --html
open ~/.safeconfig/dashboard.html
```

<div align="center">
<img src="docs/dashboard-preview.png" alt="Dashboard" width="800">
</div>

### CLI Reports

```bash
# Timeline report
python3 scripts/audit_dashboard.py --timeline 7

# Risk analysis
python3 scripts/audit_dashboard.py --risk 30

# Statistics
python3 scripts/audit_logger.py --stats
```

---

## 🔄 Rollback Capabilities

### Automatic Rollback

```python
# Auto-rollback on test failure
if not test_configuration():
    rollback_manager.rollback(target_file, backup_file)
```

### Interactive Rollback

```bash
# List available backups
python3 scripts/rollback_manager.py \
  --list openclaw.json \
  --target ~/.openclaw/openclaw.json

# Interactive selection
python3 -c "from scripts.rollback_manager import RollbackManager; \\
  RollbackManager().interactive_rollback('~/.openclaw/openclaw.json')"
```

---

## 🏗️ Architecture

```
safescheme-v2/
├── 📄 README.md                 # This file
├── 📄 README.zh.md              # Chinese documentation
├── 📄 SKILL.md                  # OpenClaw skill metadata
├── ⚙️  clawhub.json              # ClawHub publishing config
├── 📋 config.json.example       # Configuration example
│
├── 📁 scripts/
│   ├── 🔍 safescheme.py         # Phase 1: Schema validation
│   ├── 🎛️  safeconfig-v2.py     # Main workflow controller
│   ├── 📝 audit_logger.py       # Audit logging system
│   ├── 📊 audit_dashboard.py    # Visualization dashboard
│   ├── 🔄 rollback_manager.py   # Rollback management
│   └── 📢 notification_system.py # Multi-channel notifications
│
└── 📁 docs/
    └── dashboard-preview.png    # Screenshot
```

---

## 💡 Use Cases

### For Individual Users
- Protect your OpenClaw configuration
- Prevent accidental service downtime
- Track all configuration changes
- Easy rollback when things go wrong

### For Teams
- Enforce configuration review process
- Share configuration responsibility
- Audit trail for compliance
- Reduce operational errors

### For Enterprises
- Standardized deployment process
- Risk mitigation
- Compliance requirements
- Disaster recovery

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contributing Guide

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Shadow-AI.git

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
flake8 scripts/
```

---

## 📚 Documentation

- 📖 [Full Documentation](docs/)
- 🚀 [Quick Start Guide](docs/quickstart.md)
- 🛠️ [Configuration Reference](docs/config.md)
- 🔧 [Troubleshooting](docs/troubleshooting.md)
- 📊 [API Reference](docs/api.md)

---

## 🗺️ Roadmap

- [x] Core 9-phase workflow
- [x] 16-point scheme validation
- [x] Virtual environment testing
- [x] Audit logging & dashboard
- [x] Rollback management
- [ ] Web UI management interface
- [ ] Multi-user role-based access
- [ ] AI-powered configuration suggestions
- [ ] Integration with CI/CD pipelines

---

## 📜 License

MIT License - see [LICENSE](../LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by [OpenClaw](https://openclaw.ai) security best practices
- Built for the AI-native operations community
- Thanks to all contributors!

---

<div align="center">

**[⬆ Back to Top](#-safeconfig-v21)**

Made with ❤️ by [KKwang-X](https://github.com/KKwang-X)

</div>
