# SafeConfig v2.1

<p align="center">
  <a href="https://github.com/KKwang-X/Shadow-AI"><img src="https://img.shields.io/badge/version-2.1.0-blue.svg" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://openclaw.ai"><img src="https://img.shields.io/badge/OpenClaw-Compatible-orange.svg" alt="OpenClaw"></a>
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
</p>

<p align="center">
  <b>🔐 不可绕过的强制配置安全管理流程</b>
</p>

<p align="center">
  <a href="README.zh.md">中文</a> | English
</p>

---

## 🎬 演示

```
┌─────────────────────────────────────────┐
│  $ python3 safeconfig-v2.py             │
│                                         │
│  🔐 SafeConfig v2.1 - 完整流程          │
│  ====================================   │
│                                         │
│  Phase 1: 预审查 ✅ 16项检查通过        │
│  Phase 2: 变更分析 ✅ 低风险            │
│  Phase 3: 创建备份 ✅ 已备份            │
│  Phase 4: 生成审批 ✅ 请求ID: xxx       │
│  Phase 5: 等待审批 ⏳ 等待中...         │
│  Phase 6: 虚拟测试 ✅ 通过              │
│  Phase 7: 执行变更 ✅ 完成              │
│  Phase 8: 验证结果 ✅ 通过              │
│  Phase 9: 审计日志 ✅ 已记录            │
│                                         │
│  ✅ SafeConfig 流程完成                  │
└─────────────────────────────────────────┘
```

---

## ✨ 核心特性

- ✅ **9 Phase 强制流程** - 从意图声明到审计归档
- ✅ **16 项 Scheme 验证** - 基于 OpenClaw 配置规范
- ✅ **虚拟环境测试** - 隔离验证后再部署
- ✅ **双重审批机制** - 自动检查 + 人工审批
- ✅ **完整审计追踪** - 所有操作可追溯
- ✅ **一键回滚** - 自动/手动/交互式回滚
- ✅ **可视化仪表板** - HTML 报表展示

---

## 🚀 快速开始

### 安装

```bash
# 克隆到 OpenClaw workspace
git clone https://github.com/KKwang-X/Shadow-AI.git
cd Shadow-AI/safescheme-v2

# 安装到 skills 目录
cp -r . ~/.openclaw/workspace/skills/safescheme-v2
```

### 使用

```bash
cd ~/.openclaw/workspace/skills/safescheme-v2

# 执行完整 SafeConfig 流程
python3 scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:8028839180 \
  --changes "更新 API Key"

# 批准请求
python3 scripts/safeconfig-v2.py --approve <request_id>
```

---

## 📊 9 Phase 流程

| Phase | 名称 | 说明 | 强制 |
|-------|------|------|------|
| 0 | 意图声明 | 主动声明操作意图 | ✅ |
| 1 | 预审查 | 16 项 Scheme 验证 | ✅ |
| 2 | 变更分析 | 详细影响分析 | ✅ |
| 3 | 创建备份 | L1/L2/L3 三级备份 | ✅ |
| 4 | 生成审批 | 创建审批请求 | ✅ |
| 5 | 等待审批 | 用户批准/拒绝 | ✅ |
| 6 | 虚拟测试 | 隔离环境验证 | ✅ |
| 7 | 执行变更 | 生产环境应用 | ✅ |
| 8 | 验证结果 | 多维度验证 | ✅ |
| 9 | 审计日志 | 完整记录归档 | ✅ |

---

## 🛡️ 16 项 Scheme 检查

<details>
<summary>点击查看完整检查清单</summary>

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | 文件存在性 | 配置文件必须存在 |
| 2 | JSON 语法 | 必须合法 JSON |
| 3 | Scheme 结构 | 必需字段完整 |
| 4 | Meta 字段 | meta 信息完整 |
| 5 | Telegram botToken | 如启用必须配置 |
| 6 | Gateway auth token | 必须配置 |
| 7 | 类型检查 | 字段类型正确 |
| 8 | groupPolicy 值域 | 枚举值合法 |
| 9 | 依赖关系 | 启用功能有配置 |
| 10 | API Key 安全 | 不是占位符 |
| 11 | OpenClaw 状态 | 服务运行中 |
| 12 | 端口健康 | 5555 端口监听 |
| 13 | 磁盘空间 | 使用率 < 80% |
| 14 | 内存状态 | 内存充足 |
| 15 | 版本兼容 | 配置与版本匹配 |
| 16 | 日志检查 | 无严重错误 |

</details>

---

## 📈 审计仪表板

```bash
# 生成 HTML 仪表板
python3 scripts/audit_dashboard.py --html

# 打开查看
open ~/.safeconfig/dashboard.html
```

<img src="docs/dashboard-screenshot.png" alt="Dashboard" width="800">

---

## 🔄 回滚操作

```bash
# 列出备份
python3 scripts/rollback_manager.py \
  --list openclaw.json \
  --target ~/.openclaw/openclaw.json

# 回滚到指定备份
python3 scripts/rollback_manager.py \
  --rollback ~/.config-backups/openclaw.json.20260304_120000.bak \
  --target ~/.openclaw/openclaw.json
```

---

## 📁 项目结构

```
safescheme-v2/
├── README.md              # 本文档
├── README.zh.md           # 中文文档
├── SKILL.md               # OpenClaw Skill 元数据
├── scripts/
│   ├── safescheme.py      # Phase 1: Scheme 验证
│   ├── safeconfig-v2.py   # 主流程控制器
│   ├── audit_logger.py    # 审计日志系统
│   ├── audit_dashboard.py # 可视化仪表板
│   ├── rollback_manager.py # 回滚管理器
│   └── notification_system.py # 通知系统
└── docs/
    └── dashboard-screenshot.png
```

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](../LICENSE)

---

<p align="center">
  🔐 <b>SafeConfig v2.1</b> - 让配置变更更安全
  <br>
  Made with ❤️ by <a href="https://github.com/KKwang-X">KKwang-X</a>
</p>
