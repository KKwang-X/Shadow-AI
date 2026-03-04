# SafeConfig v2.1

> 🔐 **不可绕过的强制配置安全管理流程**
> 
> 基于 OpenClaw Scheme 规范的完整安全配置管理方案

---

## 核心特性

- ✅ **9 Phase 强制流程** - 从意图声明到审计归档
- ✅ **16 项 Scheme 验证** - 基于 OpenClaw 配置规范
- ✅ **虚拟环境测试** - 隔离验证后再部署
- ✅ **双重审批机制** - 自动检查 + 人工审批
- ✅ **完整审计追踪** - 所有操作可追溯
- ✅ **一键回滚** - 自动/手动/交互式回滚
- ✅ **可视化仪表板** - HTML 报表展示

---

## 架构

```
SafeConfig v2.1
├── safescheme.py          # Phase 1: Scheme 验证 (16项检查)
├── safeconfig-v2.py       # 主流程控制器 (9 Phase)
├── audit_logger.py        # 审计日志系统
├── audit_dashboard.py     # 可视化仪表板
├── rollback_manager.py    # 回滚管理器
└── notification_system.py # 通知系统
```

---

## 9 Phase 流程

| Phase | 名称 | 说明 | 强制 |
|-------|------|------|------|
| 0 | 意图声明 | 主动声明操作意图 | ✅ |
| 1 | 预审查 | Scheme + Status 16项检查 | ✅ |
| 2 | 变更分析 | 详细变更影响分析 | ✅ |
| 3 | 创建备份 | L1/L2/L3 三级备份 | ✅ |
| 4 | 生成审批 | 创建审批请求 | ✅ |
| 5 | 等待审批 | 用户批准/拒绝 | ✅ |
| 6 | 虚拟环境测试 | 隔离环境验证 | ✅ |
| 7 | 执行变更 | 生产环境应用 | ✅ |
| 8 | 验证结果 | 多维度验证 | ✅ |
| 9 | 审计日志 | 完整记录归档 | ✅ |

---

## 安装

```bash
# 克隆到 OpenClaw workspace
git clone https://github.com/KKwang-X/Shadow-AI.git
cd Shadow-AI/safescheme-v2

# 复制到工作目录
cp *.py ~/.openclaw/workspace/
```

---

## 使用方法

### 完整流程

```bash
# 执行完整 SafeConfig 流程
python3 safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:8028839180 \
  --changes "更新 Tavily API Key"
```

### 批准请求

```bash
# 批准配置变更请求
python3 safeconfig-v2.py --approve <request_id>
```

### Scheme 验证

```bash
# 单独运行 Scheme 验证
python3 safescheme.py
```

### 审计报告

```bash
# 生成统计报告
python3 audit_logger.py --stats

# 生成时间线报告
python3 audit_dashboard.py --timeline 7

# 生成 HTML 仪表板
python3 audit_dashboard.py --html
```

### 回滚操作

```bash
# 列出备份
python3 rollback_manager.py --list openclaw.json --target ~/.openclaw/openclaw.json

# 回滚到指定备份
python3 rollback_manager.py \
  --rollback ~/.config-backups/openclaw.json.20260304_120000.bak \
  --target ~/.openclaw/openclaw.json

# 交互式回滚
python3 -c "from rollback_manager import RollbackManager; RollbackManager().interactive_rollback('~/.openclaw/openclaw.json')"
```

---

## 配置

### 审批人设置

在 `safeconfig-v2.py` 中配置授权审批人：

```python
AUTHORIZED_APPROVERS = ["admin", "kk"]
```

### 通知配置

创建 `~/.safeconfig/notification.json`：

```json
{
  "telegram": {
    "enabled": true,
    "chat_id": "8028839180"
  },
  "email": {
    "enabled": false,
    "address": "admin@example.com"
  }
}
```

---

## 16 项 Scheme 检查

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

---

## 审计日志

**日志位置：** `~/.safeconfig/logs/audit_YYYYMM.jsonl`

**日志格式：**
```json
{
  "timestamp": "2026-03-04T10:00:00",
  "version": "2.1",
  "request_id": "uuid",
  "action": "config_change",
  "filepath": "~/.openclaw/openclaw.json",
  "submitter": "admin",
  "approver": "KK",
  "changes": "更新 Tavily API",
  "status": "completed",
  "phases": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
}
```

---

## 回滚策略

### 自动回滚触发条件

- Phase 8 验证失败
- 服务无法启动
- JSON 语法错误
- 用户明确要求

### 回滚流程

```
1. 停止服务
2. 恢复备份
3. 验证恢复
4. 启动服务
5. 功能验证
```

---

## 最佳实践

### 1. 任何配置变更必须走 SafeConfig

```bash
# ❌ 错误：直接修改
vim ~/.openclaw/openclaw.json

# ✅ 正确：使用 SafeConfig
python3 safeconfig-v2.py --file ... --approver ... --changes ...
```

### 2. 高风险变更需要额外注意

- 修改 gateway 配置
- 更新核心服务
- 删除关键字段

### 3. 定期检查审计日志

```bash
# 每周检查
python3 audit_dashboard.py --timeline 7

# 查看风险分析
python3 audit_dashboard.py --risk 30
```

### 4. 保持备份清洁

```bash
# 定期清理旧备份
python3 rollback_manager.py --cleanup 10
```

---

## 故障排除

### 预审查失败

```bash
# 查看详细错误
python3 safescheme.py
# 根据错误提示修复
```

### 审批超时

```bash
# 重新生成审批请求
python3 safeconfig-v2.py --file ... --approver ... --changes ...
```

### 回滚失败

```bash
# 手动恢复
python3 rollback_manager.py --list <filename> --target <filepath>
# 选择备份回滚
```

---

## 开发计划

- [x] P0: Scheme 验证器
- [x] P0: 完整流程控制
- [x] P1: 审计日志系统
- [x] P1: 回滚机制
- [x] P1: 通知系统
- [ ] P2: Web UI 管理界面
- [ ] P2: 多用户权限管理
- [ ] P2: 自动修复建议

---

## 许可证

MIT License - 详见 LICENSE

---

## 贡献

欢迎提交 PR 和 Issue！

---

<p align="center">
  🔐 SafeConfig v2.1 - 让配置变更更安全
</p>
