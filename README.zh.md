# Shadow-AI

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-贡献者-blue?style=flat-square" alt="OpenClaw 贡献者">
  <img src="https://img.shields.io/badge/Python-3.8+-green?style=flat-square" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT License">
</p>

<p align="center">
  <a href="README.md">English</a> | <b>中文</b>
</p>

---

一套专为 **AI Agent 安全运维**而生的生产级工具集——源于真实事故：自主 Agent 在无人监督下写坏了生产配置。

> 💡 *"我踩过很多坑，这样你就不用踩了。"*
> — KK，OpenClaw 贡献者

---

## 🛡️ 解决什么问题

现代 AI Agent（OpenClaw、Claude Code 等）可以执行 shell 命令、修改文件。这很强大，但也很危险：

- 模型会**幻觉**出不存在的 CLI 参数
- Agent 在没有备份、没有审批的情况下**直接写入关键配置**
- 一次错误的编辑就能让生产服务宕机——且无法回滚

**SafeConfig** 及其工具生态为 Agent 添加了一道无法绕过的系统级安全拦截。

---

## 🗂️ 仓库结构

```
Shadow-AI/
├── safedeploy.py              # 一键安全部署
├── safescheme-v2/             # 完整 9-Phase 配置变更流程
└── skills/
    ├── safeconfig/            # 核心配置守卫（v1）+ PreToolUse Hook
    ├── qqmail-sender/         # QQ 邮箱 SMTP 发送
    └── skill-security-auditor/ # Skill 安全审计
```

---

## 🚀 项目介绍

### 🔒 SafeConfig v1 — 配置守卫

在关键配置文件被修改**之前**拦截操作。

**工作原理：**

`pre-tool-hook.py` 注册为 Claude Code 的 `PreToolUse` Hook。每当 Agent 调用 `Edit`、`Write`、`Bash` 工具时，Hook 会检查目标文件是否属于关键配置。若命中，操作在**系统层面被阻断**——Agent 必须先完成 safeconfig 审批流程才能继续。

```
Agent 调用 Edit ~/.openclaw/openclaw.json
        ↓
PreToolUse Hook 触发（工具执行前）
        ↓
检测到关键配置 → exit 2 → 工具被阻断
        ↓
Agent 必须先完成 safeconfig 流程
```

**快速开始：**
```bash
# 检查文件是否为关键配置
python3 skills/safeconfig/safeconfig.py --check ~/.openclaw/openclaw.json

# 备份 + 审批流程
python3 skills/safeconfig/safeconfig.py \
  --backup ~/.openclaw/openclaw.json \
  --approver telegram:<审批人ID> \
  --changes "更新 API Key"

# 在另一个终端批准请求
python3 skills/safeconfig/safeconfig.py --approve <request_id>
```

**Hook 安装**（一次性配置）：

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

> 项目自带的 `.claude/settings.json` 已预配置好此 Hook，克隆即用。

---

### 🔒 SafeConfig v2 — 9-Phase 完整流程

针对高风险配置变更的结构化变更管理流程。

```
Phase 1 → 预审查（16 项 Scheme 验证）
Phase 2 → 变更分析
Phase 3 → 三级备份
Phase 4 → 生成审批请求
Phase 5 → 等待审批（每 5 秒轮询，最多 30 分钟）
Phase 6 → 虚拟环境测试
Phase 7 → 执行变更（交互式确认）
Phase 8 → 验证结果
Phase 9 → 审计日志归档
```

**快速开始：**
```bash
python3 safescheme-v2/scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:<审批人ID> \
  --changes "轮换网关认证 Token"
```

---

### 🚀 SafeDeploy — 一键安全部署

自动完成验证、修复、备份、部署全流程。

```bash
# 仅检查（不修改任何文件）
python3 safedeploy.py check

# 检查并自动修复问题
python3 safedeploy.py fix

# 带审批的完整部署流程
python3 safedeploy.py deploy --approver telegram:<审批人ID> --changes "更新配置"
```

**自动修复项：**

| 问题 | 修复方式 |
|------|---------|
| 无效参数（如 `--daemon`） | 自动移除 |
| JSON 尾随逗号 | 自动清理 |
| 缺失必填字段 | 注入默认值 |

📖 [完整 SafeDeploy 文档](SAFEDEPLOY.md)

---

### 🔍 Skill 安全审计器

扫描所有已安装 Skill 中的安全问题：硬编码密钥、危险 shell 命令模式、缺失输入校验、权限过宽等。

```bash
python3 skills/skill-security-auditor/scripts/auditor.py
```

---

### 📧 QQMail 邮件发送

基于 QQ 邮箱 SMTP 的邮件发送工具——国内网络最稳定的方案，无需翻墙。

```bash
export QQMAIL_EMAIL="your-qq@qq.com"
export QQMAIL_AUTH_CODE="your-auth-code"

python3 skills/qqmail-sender/qqmail.py "recipient@example.com" "主题" "正文"
```

📖 [配置指南](skills/qqmail-sender/README.md)

---

## 🛠️ Skill 一览

| Skill | 用途 | 状态 |
|-------|------|------|
| [safeconfig](skills/safeconfig/) | 配置守卫 + PreToolUse Hook | ✅ 生产就绪 |
| [safescheme-v2](safescheme-v2/) | 9-Phase 变更管理流程 | ✅ 生产就绪 |
| [skill-security-auditor](skills/skill-security-auditor/) | Skill 安全扫描 | ✅ 生产就绪 |
| [qqmail-sender](skills/qqmail-sender/) | QQ 邮箱 SMTP 发送 | ✅ 生产就绪 |

---

## 📚 踩坑实录（血泪教训）

### 教训 1：永远不要相信模型生成的参数
```bash
# ❌ 错误：模型幻觉生成的参数
ExecStart=/path/to/openclaw gateway start --daemon
# 结果：服务崩溃，"unknown option '--daemon'"

# ✅ 正确：查完 --help 验证后
ExecStart=/path/to/openclaw gateway start
```

### 教训 2：修改前必须备份
```
~/.config-backups/openclaw.service.20250303_234439.bak
```

### 教训 3：每次修改后都要验证服务状态
```bash
sudo systemctl daemon-reload && sudo systemctl restart openclaw
sudo systemctl status openclaw --no-pager
```

---

## 🤝 贡献

欢迎贡献，特别是：
- 新的安全检查规则和更多配置格式支持
- 与其他 AI Agent 平台的集成（Cursor、Windsurf 等）
- 更多 Skill 安全审计规则

---

## 📄 许可证

MIT — 详见 [LICENSE](LICENSE)

---

<p align="center">
  用 ❤️ 和血泪经验构建 by <a href="https://github.com/KKwang-X">KK</a><br>
  <sub>OpenClaw 贡献者 · 安全倡导者 · AI Agent 实践者</sub>
</p>
