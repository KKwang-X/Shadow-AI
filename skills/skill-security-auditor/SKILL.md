---
name: skill-security-auditor
description: Skill 安全审计工具，检查已安装 skill 的安全风险
version: 1.0.0
author: KKwang-X
license: MIT
tags: [security, audit, skill-management]
requirements:
  - python3 >= 3.8
install: |
  git clone https://github.com/KKwang-X/Shadow-AI.git
  cp -r Shadow-AI/skills/skill-security-auditor ~/.openclaw/workspace/skills/
usage: |
  python3 scripts/auditor.py
  python3 scripts/auditor.py --json
---
