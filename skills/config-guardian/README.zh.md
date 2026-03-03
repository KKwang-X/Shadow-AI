---
name: config-guardian
description: 配置修改安全守护技能。在修改关键配置文件（openclaw.json、systemd服务、nginx等）前强制执行安全检查：验证参数有效性、自动备份、二次确认。Use when: (1) 修改 ~/.openclaw/openclaw.json, (2) 修改 /etc/systemd/system/ 下的服务配置, (3) 修改 nginx/ssh 等系统配置, (4) 任何可能影响服务运行的配置变更。
---

# Config Guardian - 安全配置管理

> <strong>⚠️ 为什么有这个 Skill</strong><br>
> 当 AI Agent 拥有 `exec` 权限时，一个幻觉生成的参数就能让生产服务崩溃。这个 Skill 诞生于真实的痛苦——我曾因为模型建议的 `--daemon`（一个不存在的参数）在一晚之内让 OpenClaw 网关崩溃了 3 次。

## 核心理念

**所有关键配置修改必须遵循以下流程：**

1. **先验证，后修改** — 使用 `--help` 或文档确认参数存在
2. **自动备份** — 修改前创建带时间戳的备份
3. **二次确认** — 向用户展示修改内容，获得明确确认
4. **修改后验证** — 检查服务状态确保正常

## 关键配置文件列表

| 文件路径 | 类型 | 风险等级 |
|---------|------|---------|
| `~/.openclaw/openclaw.json` | OpenClaw 配置 | 🔴 高 |
| `/etc/systemd/system/*.service` | Systemd 服务 | 🔴 高 |
| `/etc/nginx/nginx.conf` | Nginx 配置 | 🟡 中 |
| `~/.ssh/config` | SSH 配置 | 🟡 中 |

## 踩坑实录（血泪教训）

### 教训 1：永远不要相信模型生成的参数
```bash
# ❌ 错误：模型建议的参数
ExecStart=/home/admin/.npm-global/bin/openclaw gateway start --daemon
# 结果：服务崩溃，报错 "unknown option '--daemon'"

# ✅ 正确：查完 --help 后
ExecStart=/home/admin/.npm-global/bin/openclaw gateway start
# 结果：服务正常启动
```

### 教训 2：修改前必须备份
没有备份，一次错误的编辑就能让你手忙脚乱。Config Guardian 自动创建带时间戳的备份：
```
~/.config-backups/openclaw.service.20250303_234439.bak
```

### 教训 3：每次修改后都要验证
```bash
sudo systemctl daemon-reload
sudo systemctl restart openclaw
sudo systemctl status openclaw --no-pager  # 必须检查！
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/KKwang-X/Shadow-AI.git
cd Shadow-AI

# 添加执行权限
chmod +x skills/config-guardian/config-guardian.py

# 可选：添加到 PATH
sudo cp skills/config-guardian/config-guardian.py /usr/local/bin/
```

## 使用方法

### 检查是否为关键配置
```bash
python3 config-guardian.py --check ~/.openclaw/openclaw.json
# 输出：关键配置: 是
```

### 备份配置文件
```bash
python3 config-guardian.py --backup /etc/systemd/system/myapp.service
# 输出：✅ 备份已创建: ~/.config-backups/myapp.service.20250303_234439.bak
```

### 验证 Systemd 配置
```bash
python3 config-guardian.py --validate-systemd /etc/systemd/system/myapp.service
# 输出：✅ systemd 配置验证通过
```

## 安全检查清单

修改任何关键配置前：

```
□ 该参数在当前版本是否存在？（查 --help）
□ 修改前是否已备份原配置？
□ 是否已向用户展示修改内容？
□ 是否获得用户明确确认？
□ 修改后服务状态是否正常？
```

## 与 OpenClaw/Codex 集成

添加到你的 Agent 指令中：

```markdown
## 配置安全规则

修改关键配置文件时：
1. 运行 `config-guardian.py --check <filepath>` 识别关键配置
2. 运行 `config-guardian.py --backup <filepath>` 修改前备份
3. 对于 systemd：运行 `config-guardian.py --validate-systemd <file>`
4. 向用户展示确切的变更内容
5. 获得明确确认（"确认"、"执行"、"ok"）
6. 修改后验证服务状态
```

## 常见错误预防

| 错误场景 | 预防措施 |
|---------|---------|
| 使用不存在的参数 | 修改前执行 `--help` 验证 |
| 配置语法错误 | 使用 `systemd-analyze verify` 检查 |
| 服务无法启动 | 修改前备份，保留回滚能力 |
| 权限不足 | 提前检查文件权限，必要时使用 sudo |

## 回滚方法

如果修改后出现问题：

```bash
# 从备份恢复
cp ~/.config-backups/myapp.service.20250303_234439.bak /etc/systemd/system/myapp.service

# 重载并重启
sudo systemctl daemon-reload
sudo systemctl restart myapp
```

## 为什么这对 AI Agent 很重要

拥有 `exec` 权限的 AI Agent 可以：
- 执行任意 shell 命令
- 修改系统配置
- 启动/停止服务

**没有防护栏，这很危险。** 模型可能：
- 幻觉生成不存在的参数
- 生成语法错误的配置
- 未经验证就应用变更

**Config Guardian 添加了本该内置的安全层。**

## 许可证

MIT 许可证 - 详见 [LICENSE](../../LICENSE)

---

<p align="center">
  用 ❤️ 和血泪教训构建 by <a href="https://github.com/KKwang-X">KK</a>
</p>
