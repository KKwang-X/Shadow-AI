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

## 🎯 关于我

**OpenClaw 贡献者** | AI Agent 实践者 | 生产安全倡导者

我是 KK，北京某互联网大厂商业分析师。通过大量 AI Agent 实践，我深刻认识到：**当模型拥有 exec 权限时，安全必须是第一位的**。

> 💡 "我踩过很多坑，这样你就不用踩了。"

这个仓库记录了我构建 AI Agent 系统的历程，特别关注**安全配置管理**和**生产部署最佳实践**。

---

## 🚀 项目

### Shadow-AI (原版)
一个将 **GKD 前端控制器**与**大语言模型**结合的 AI 引擎，通过语音/文本命令实现 Android 设备自动化。

### SafeConfig ⭐ (精选 Skill)
一个为 OpenClaw/Codex 设计的安全优先 Skill，在修改关键配置前强制执行严格的安全检查。

**为什么这很重要：**
当 AI Agent 拥有 `exec` 权限时，一个幻觉生成的参数就能让生产服务崩溃。我曾因为 `--daemon`（一个不存在的参数）导致 OpenClaw 网关反复崩溃，深有体会。

**核心功能：**
- ✅ 修改前验证参数存在性
- ✅ 自动备份（带时间戳）
- ✅ 强制用户确认
- ✅ 修改后服务状态验证
- ✅ 支持 openclaw.json、systemd、nginx、ssh 配置

**快速开始：**
```bash
python3 skills/safeconfig/safeconfig.py --check ~/.openclaw/openclaw.json
python3 skills/safeconfig/safeconfig.py --backup /etc/systemd/system/myapp.service
```

---

## 🛡️ 安全第一理念

### 问题所在
现代 AI Agent（OpenClaw、Claude Code 等）可以执行 shell 命令。这很强大，但也很危险：
- 模型可能幻觉生成不存在的参数
- 配置语法错误可能导致服务崩溃
- 缺乏内置安全防护

### 解决方案
**SafeConfig** 实现了 4 步安全工作流：

1. **验证** — 使用任何参数前先查 `--help`
2. **备份** — 修改前总是备份
3. **确认** — 展示变更，获得用户明确确认
4. **验证** — 修改后检查服务状态

### 实际效果
| 使用 SafeConfig 之前 | 使用 SafeConfig 之后 |
|------------------------|----------------------|
| 一晚服务崩溃 3 次 | 零生产事故 |
| `--daemon` 参数幻觉 | 所有参数都经过验证 |
| 无法回滚 | 自动时间戳备份 |
| 静默失败 | 需要明确确认 |

---

## 📚 踩坑实录（血泪教训）

### 教训 1：永远不要相信模型生成的参数
```bash
# ❌ 错误：模型建议的
ExecStart=/path/to/openclaw gateway start --daemon

# ✅ 正确：查完 --help 后
ExecStart=/path/to/openclaw gateway start
```

### 教训 2：关键配置必须备份
```bash
# Config Guardian 自动备份
~/.config-backups/openclaw.service.20250303_234439.bak
```

### 教训 3：每次修改后都要验证
```bash
sudo systemctl daemon-reload
sudo systemctl restart service
sudo systemctl status service --no-pager  # 必须检查！
```

---

## 🛠️ Skill 集合

| Skill | 描述 | 状态 |
|-------|-------------|--------|
| [SafeConfig](skills/safeconfig/) | 安全配置管理 | ✅ 生产就绪 |
| 更多 coming... | | 🚧 开发中 |

---

## 🤝 贡献

欢迎贡献！特别是：
- 额外的安全检查
- 支持更多配置格式
- 与其他 AI Agent 平台集成

---

## 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)

---

<p align="center">
  用 ❤️ 和大量 ☕ 构建 by <a href="https://github.com/KKwang-X">KK</a>
</p>
<p align="center">
  <sub>OpenClaw 贡献者 • 安全倡导者 • AI Agent 实践者</sub>
</p>
