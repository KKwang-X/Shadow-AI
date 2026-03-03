# SafeDeploy - 安全部署工具

> 🇨🇳 **踩过无数坑换来的 OpenClaw 部署神器**
> 
> 曾因 `--daemon` 参数崩溃 3 次，曾因未备份配置丢失重要设置，曾因未测试直接上线引发故障... 这个工具就是为避免这些血泪教训而生。

---

## 💡 为什么需要 SafeDeploy？

### 血泪教训

| 事故 | 原因 | 损失 | SafeDeploy 解决方案 |
|------|------|------|---------------------|
| 服务崩溃 3 次 | `--daemon` 参数不存在 | 3 小时停机 | 自动检测并移除无效参数 |
| 配置丢失 | 未备份直接修改 | 重要设置丢失 | 自动备份所有关键配置 |
| 上线故障 | 未验证直接部署 | 用户投诉 | 部署前强制验证 |
| 误操作 | 单人操作无复核 | 生产事故 | 审批人机制 |

### 核心原则

**验证 → 修复 → 审批 → 部署 → 验证**

宁可多花 5 分钟检查，也不要花 5 小时恢复。

---

## 🚀 功能特性

### 1. 部署前验证（Pre-Deploy Check）

- ✅ JSON 语法检查
- ✅ Systemd 配置验证
- ✅ 参数有效性检查（查 `--help`）
- ✅ 服务状态检查
- ✅ Gateway 连接性测试

### 2. 自动修复（Auto-Fix）

发现即修复，无需人工干预：

| 问题 | 自动修复 |
|------|----------|
| `--daemon` 等无效参数 | 自动移除 |
| JSON 尾随逗号 | 自动删除 |
| 缺失必要字段 | 自动补全默认值 |
| 过期 Token | 标记提醒 |

### 3. 审批流程（Approval Workflow）

高风险操作必须经第二人确认：

```
提交变更 → 创建审批请求 → 审批人批准 → 执行部署
```

- 支持 Telegram/Email 通知
- 30 分钟超时机制
- 完整审计日志

### 4. 原子化部署

- 自动备份原配置
- 失败自动回滚
- 部署后健康检查

---

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/KKwang-X/Shadow-AI.git
cd Shadow-AI

# 使用 SafeDeploy
python3 safedeploy.py --help
```

---

## 🎯 使用方法

### 模式 1：仅检查（Check）

```bash
python3 safedeploy.py check
```

只验证配置，不修改任何文件。

### 模式 2：检查并修复（Fix）

```bash
python3 safedeploy.py fix
```

发现问题自动修复，适合日常维护。

### 模式 3：完整部署（Deploy）

```bash
# 基础部署
python3 safedeploy.py deploy

# 带审批的部署（推荐生产环境）
python3 safedeploy.py deploy --approver telegram:admin --changes "更新SSL证书"

# 自动确认（适合CI/CD）
python3 safedeploy.py deploy --yes
```

### 审批操作

```bash
# 批准请求
python3 safedeploy.py --approve req_20250304_123456_abc123

# 拒绝请求
python3 safedeploy.py --reject req_20250304_123456_abc123
```

---

## 🏗️ 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 验证配置                                                 │
│     ├── JSON 语法检查 ✅                                      │
│     ├── Systemd 配置验证 ✅                                   │
│     └── 参数有效性检查 ✅                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. 自动修复（发现问题时）                                    │
│     ├── 移除 --daemon 等无效参数 ✅                           │
│     ├── 修复 JSON 语法错误 ✅                                 │
│     └── 补全缺失字段 ✅                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. 创建备份                                                 │
│     └── ~/.config-backups/xxx.bak ✅                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 审批流程（如指定了审批人）                                │
│     ├── 发送审批请求 → Telegram/Email                         │
│     ├── 等待审批人批准/拒绝                                   │
│     └── 30分钟超时自动取消                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. 执行部署                                                 │
│     ├── systemctl restart openclaw ✅                         │
│     └── 健康检查确认 ✅                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    🎉 部署成功！
```

---

## 🔐 审批流程详解

### 为什么需要审批？

| 场景 | 无审批 | 有审批 |
|------|--------|--------|
| 单人操作 | 风险高 | 有审计 trail |
| 团队协作 | 无 oversight | 第二人确认 |
| 生产环境 | 直接修改 | 受控发布 |
| 合规要求 | 无记录 | 完整日志 |

### 审批消息示例

```
🔐 SafeDeploy 审批请求

请求ID: req_20250304_123456_abc123
时间: 2026-03-04 12:34:56

📝 变更说明:
更新SSL证书，添加新域名支持

🔧 自动修复记录:
✅ 移除无效参数 --daemon
✅ 修复JSON尾随逗号

⚠️ 这是一个关键配置变更，需要您的审批。

✅ 回复 "批准" 或执行:
   python3 safedeploy.py --approve req_xxx

❌ 回复 "拒绝" 或执行:
   python3 safedeploy.py --reject req_xxx

⏰ 审批将在30分钟后过期
```

---

## 🛡️ 安全特性

### 自动备份

每次部署前自动备份关键配置：
```
~/.config-backups/
├── openclaw.json.20250304_123456.bak
├── openclaw.service.20250304_123501.bak
└── ...
```

### 原子化更新

- 验证通过后才执行修改
- 失败自动回滚到备份
- 部署失败不中断服务

### 审计日志

所有操作记录在案：
```
~/.safeconfig/approvals/
├── req_20250304_123456_abc123.json
├── req_20250304_123501_def456.json
└── ...
```

---

## 📋 检查清单

SafeDeploy 会自动检查以下项目：

- [ ] JSON 配置文件语法正确
- [ ] Systemd 服务配置有效
- [ ] OpenClaw 参数存在（查 `--help`）
- [ ] 无无效参数（如 `--daemon`）
- [ ] Telegram Bot Token 已配置
- [ ] Gateway Auth Token 有效
- [ ] 服务当前运行状态正常
- [ ] Gateway 连接性良好

---

## 🔧 常见问题

### Q: 自动修复会修改我的配置吗？

A: 只有在 `fix` 或 `deploy` 模式下才会修复。`check` 模式只检查不修改。

### Q: 审批流程可以跳过吗？

A: 可以，不指定 `--approver` 即可。但生产环境强烈建议启用。

### Q: 如何查看审批历史？

A: 查看 `~/.safeconfig/approvals/` 目录下的 JSON 文件。

### Q: 部署失败如何回滚？

A: SafeDeploy 会自动备份，手动恢复：
```bash
cp ~/.config-backups/openclaw.json.xxx.bak ~/.openclaw/openclaw.json
sudo systemctl restart openclaw
```

---

## 📝 最佳实践

### 开发环境
```bash
# 快速迭代
python3 safedeploy.py fix
```

### 测试环境
```bash
# 验证后部署
python3 safedeploy.py check && python3 safedeploy.py deploy
```

### 生产环境
```bash
# 完整流程：验证 → 修复 → 审批 → 部署
python3 safedeploy.py deploy --approver telegram:ops_team --changes "更新生产配置"
```

---

## 🤝 与其他工具集成

### CI/CD 集成

```yaml
# GitHub Actions 示例
- name: SafeDeploy
  run: |
    python3 safedeploy.py deploy --yes
```

### Cron 定时任务

```bash
# 每日检查配置健康度
0 9 * * * cd /path/to/openclaw && python3 safedeploy.py check
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](../LICENSE)

---

<p align="center">
  🔧 用 <strong>SafeDeploy</strong>，让每一次部署都安心
  <br>
  <sub>踩过无数坑，只为让你少走弯路</sub>
</p>
