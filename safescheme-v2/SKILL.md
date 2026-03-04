---
name: safescheme-v2
description: SafeConfig v2.1 - 不可绕过的强制配置安全管理流程。基于 OpenClaw Scheme 规范的完整安全配置管理，包含 9 Phase 强制流程、16 项验证、虚拟环境测试、审计追踪、自动回滚。
version: 2.1.0
author: KKwang-X
license: MIT
tags: [security, config-management, audit, rollback, deployment]
requirements:
  - python3 >= 3.8
  - openclaw
install: |
  git clone https://github.com/KKwang-X/Shadow-AI.git
  cp -r Shadow-AI/skills/safescheme-v2 ~/.openclaw/workspace/skills/
usage: |
  # 完整流程
  python3 scripts/safeconfig-v2.py --file ~/.openclaw/openclaw.json --approver telegram:USER_ID --changes "变更说明"
  
  # 批准请求
  python3 scripts/safeconfig-v2.py --approve REQUEST_ID
  
  # Scheme 验证
  python3 scripts/safescheme.py
  
  # 审计报告
  python3 scripts/audit_dashboard.py --html
---

# SafeConfig v2.1

🔐 **不可绕过的强制配置安全管理流程**

## 核心特性

- ✅ **9 Phase 强制流程** - 从意图声明到审计归档
- ✅ **16 项 Scheme 验证** - 基于 OpenClaw 配置规范
- ✅ **虚拟环境测试** - 隔离验证后再部署
- ✅ **双重审批机制** - 自动检查 + 人工审批
- ✅ **完整审计追踪** - 所有操作可追溯
- ✅ **一键回滚** - 自动/手动/交互式回滚
- ✅ **可视化仪表板** - HTML 报表展示

## 快速开始

```bash
# 执行完整 SafeConfig 流程
python3 scripts/safeconfig-v2.py \
  --file ~/.openclaw/openclaw.json \
  --approver telegram:8028839180 \
  --changes "更新 API Key"

# 批准请求
python3 scripts/safeconfig-v2.py --approve <request_id>
```

## 9 Phase 流程

1. **意图声明** - 主动声明操作意图
2. **预审查** - 16 项 Scheme 验证
3. **变更分析** - 详细影响分析
4. **创建备份** - 三级备份策略
5. **生成审批** - 创建审批请求
6. **等待审批** - 用户批准/拒绝
7. **虚拟环境测试** - 隔离验证
8. **执行变更** - 生产环境应用
9. **验证结果** - 多维度验证
10. **审计日志** - 完整记录归档

## 文档

详见 [README.md](README.md)
