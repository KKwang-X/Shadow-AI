---
name: safescheme-v2
description: SafeConfig v2.1 - 不可绕过的强制配置安全管理流程。基于 OpenClaw Scheme 规范的完整安全配置管理，包含 9-Phase 强制流程（预审查→备份→审批→虚拟测试→变更→验证→审计）、Scheme 结构验证、虚拟环境测试、审计追踪、自动回滚。支持 --new-content-file 参数与 PreToolUse Hook 无缝联动。Use when: (1) Agent 通过 safeconfig hook 触发了配置变更拦截, (2) 需要对关键配置进行结构化变更管理, (3) 需要自动备份+审批+验证+回滚保障。
version: 2.1.0
author: KKwang-X
license: MIT
tags: [security, config-management, audit, rollback, deployment, openclaw]
requirements:
  - python3 >= 3.8
  - openclaw
install: |
  git clone https://github.com/KKwang-X/Shadow-AI.git
  cp -r Shadow-AI/safescheme-v2 ~/.openclaw/workspace/skills/
usage: |
  # 完整流程（配合 hook 捕获的内容文件）
  python3 scripts/safeconfig-v2.py \
    --file ~/.openclaw/openclaw.json \
    --approver telegram:USER_ID \
    --changes "变更说明" \
    --new-content-file /tmp/safeconfig_proposed_xyz.json

  # 批准 / 拒绝请求
  python3 scripts/safeconfig-v2.py --approve REQUEST_ID
  python3 scripts/safeconfig-v2.py --reject REQUEST_ID

  # 手动回滚
  python3 scripts/rollback_manager.py \
    --target ~/.openclaw/openclaw.json \
    --rollback ~/.config-backups/openclaw.json.20260320_143022.bak

  # Scheme 验证（仅结构校验）
  python3 scripts/safescheme.py
---

# SafeConfig v2.1

🔐 **不可绕过的强制配置安全管理流程**

## 核心特性

- ✅ **9-Phase 强制流程** — 预审查→变更分析→备份→审批→等待→虚拟测试→应用→验证→审计
- ✅ **Scheme 结构验证** — 基于 OpenClaw 配置规范校验字段、类型、依赖关系
- ✅ **虚拟环境测试** — 将拟议内容写入隔离环境验证后再部署（Phase 6）
- ✅ **原子写入** — `--new-content-file` 模式下直接复制，不依赖 Agent 交互输入（Phase 7）
- ✅ **自动回滚** — Phase 8 验证失败时自动调用 RollbackManager 恢复备份
- ✅ **双重审批** — 权限校验 + 幂等处理，防止重复操作
- ✅ **完整审计追踪** — 所有操作追加到 JSONL 审计日志

## 快速开始

```bash
# 完整流程（Agent 模式）
python3 scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:<审批人ID> \
  --changes "更新 API Key" \
  --new-content-file /tmp/safeconfig_proposed_xyz.json

# 批准请求
python3 scripts/safeconfig-v2.py --approve <request_id>
```

## 9-Phase 流程

| Phase | 名称 | 说明 |
|-------|------|------|
| 1 | 预审查 | Scheme 结构校验（不检查服务状态，避免服务停止时阻塞） |
| 2 | 变更分析 | 变更影响分析 |
| 3 | 创建备份 | 带时间戳备份至 `~/.config-backups/` |
| 4 | 生成审批 | 创建审批请求，通知审批人 |
| 5 | 等待审批 | 每 5 秒轮询，最多 30 分钟 |
| 6 | 虚拟测试 | 拟议内容→隔离环境→Scheme 验证 |
| 7 | 执行变更 | 原子写入（`--new-content-file`）或交互式确认 |
| 8 | 验证结果 | 重新校验，失败时自动回滚 |
| 9 | 审计归档 | JSONL 记录追加到审计日志 |

## 文档

详见 [README.md](../README.zh.md)

