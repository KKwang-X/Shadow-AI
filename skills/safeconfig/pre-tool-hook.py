#!/usr/bin/env python3
"""
SafeConfig PreToolUse Hook

在 Claude Code 执行 Edit / Write / Bash 工具前自动拦截，
检测目标文件是否为关键配置文件。若是，则阻止直接修改，
强制 agent 必须通过 safeconfig 安全流程。

注册方式（~/.claude/settings.json 或项目 .claude/settings.json）:
  "PreToolUse": [
    {
      "matcher": "Edit|Write|Bash",
      "hooks": [{"type": "command", "command": "python3 /path/to/pre-tool-hook.py"}]
    }
  ]

返回值:
  exit 0  → 允许工具继续执行
  exit 2  → 阻止工具执行（stdout 内容会展示给 Claude）
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

# ──────────────────────────────────────────────
# 关键配置文件匹配规则（正则表达式）
# ──────────────────────────────────────────────
CRITICAL_PATTERNS = [
    # OpenClaw 配置
    r"(^|/)\.openclaw/.*\.json$",
    r"(^|/)openclaw\.json$",
    # Systemd 服务
    r"^/etc/systemd/system/.*\.(service|timer|socket|mount)$",
    r"^/etc/systemd/user/.*\.(service|timer|socket|mount)$",
    # Nginx
    r"^/etc/nginx/",
    # SSH
    r"(^|/)\.ssh/(config|authorized_keys|sshd_config)$",
    r"^/etc/ssh/sshd_config",
    # Claude Code 自身设置（防止 agent 修改自身配置）
    r"(^|/)\.claude/settings.*\.json$",
]

# ──────────────────────────────────────────────
# 关键配置文件路径检测
# ──────────────────────────────────────────────

def _normalize(path: str) -> list[str]:
    """返回路径的多种形态用于匹配（原始、展开 ~、绝对路径）"""
    variants = [path]
    try:
        expanded = str(Path(path).expanduser())
        variants.append(expanded)
        resolved = str(Path(path).expanduser().resolve())
        variants.append(resolved)
    except Exception:
        pass
    return list(set(variants))


def is_critical_path(filepath: str) -> bool:
    """判断文件路径是否属于关键配置"""
    for variant in _normalize(filepath):
        for pattern in CRITICAL_PATTERNS:
            if re.search(pattern, variant):
                return True
    return False


# ──────────────────────────────────────────────
# Bash 命令分析：检测是否写入关键配置文件
# ──────────────────────────────────────────────

# 匹配"写操作 + 目标路径"的常见模式
_BASH_WRITE_PATTERNS = [
    r">\s*([^\s;|&>]+)",                           # > file  /  >> file
    r"tee(?:\s+-a)?\s+([^\s;|&]+)",               # tee / tee -a
    r"sed\s+(?:\S+\s+)*-i\S*\s+.*?\s+([^\s;|&]+)$",  # sed -i ... file
    r"cp\s+\S+\s+([^\s;|&]+)$",                   # cp src DEST
    r"mv\s+\S+\s+([^\s;|&]+)$",                   # mv src DEST
    r"install\s+.*\s+([^\s;|&]+)$",               # install ... DEST
    r"truncate\s+.*\s+([^\s;|&]+)$",              # truncate ... file
]


def find_critical_bash_target(command: str) -> str | None:
    """
    分析 Bash 命令，返回被写入的关键配置路径（若有）。
    若检测不到则返回 None。
    """
    for pattern in _BASH_WRITE_PATTERNS:
        for match in re.finditer(pattern, command):
            candidate = match.group(1).strip().strip("'\"")
            if candidate and is_critical_path(candidate):
                return candidate
    return None


# ──────────────────────────────────────────────
# Bypass 机制：紧急情况可通过环境变量跳过
# ──────────────────────────────────────────────

def is_bypass_enabled() -> bool:
    """检查是否设置了紧急 bypass 环境变量"""
    return os.environ.get("SAFECONFIG_BYPASS", "").strip() == "1"


# ──────────────────────────────────────────────
# 生成拦截消息
# ──────────────────────────────────────────────

def capture_proposed_content(tool_name: str, tool_input: dict, target_path: str) -> str | None:
    """
    从 Edit/Write 工具输入中提取拟议新内容，写入临时文件并返回路径。
    Bash 工具无法可靠提取内容，返回 None。
    """
    content: str | None = None

    if tool_name == "Write":
        content = tool_input.get("content")

    elif tool_name == "Edit":
        # Edit 工具提供 old_string + new_string，我们需要读原文件并做替换
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)
        try:
            with open(Path(file_path).expanduser(), "r", encoding="utf-8") as f:
                original = f.read()
            if replace_all:
                content = original.replace(old_string, new_string)
            else:
                content = original.replace(old_string, new_string, 1)
        except Exception:
            content = None

    if content is None:
        return None

    try:
        safeconfig_dir = Path("~/.safeconfig").expanduser()
        safeconfig_dir.mkdir(parents=True, exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", prefix="safeconfig_proposed_",
            dir=safeconfig_dir, delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception:
        return None


def build_block_message(target_path: str, tool_name: str,
                        proposed_file: str | None = None) -> str:
    repo = os.path.expanduser("~/Shadow-AI")
    safeconfig_v1 = f"{repo}/skills/safeconfig/safeconfig.py"
    safeconfig_v2 = f"{repo}/safescheme-v2/scripts/safeconfig-v2.py"

    new_content_flag = (
        f" \\\n    --new-content-file {proposed_file}"
        if proposed_file else ""
    )

    return f"""
╔══════════════════════════════════════════════════════════════╗
║           🚨 SafeConfig Hook — 操作已拦截                    ║
╚══════════════════════════════════════════════════════════════╝

工具:     {tool_name}
目标文件: {target_path}

⛔ 禁止直接修改关键配置文件。

必须通过 safeconfig 安全流程才能继续：

─── 方案 A：v1 基础流程（备份 + 审批）───────────────────────
  python3 {safeconfig_v1} \\
    --backup {target_path} \\
    --approver telegram:<审批人ID> \\
    --changes "本次变更说明"

─── 方案 B：v2 完整 9-Phase 流程（推荐）────────────────────
  python3 {safeconfig_v2} \\
    --file {target_path} \\
    --approver telegram:<审批人ID> \\
    --changes "本次变更说明"{new_content_flag}

─── 紧急 Bypass（须有正当理由）─────────────────────────────
  export SAFECONFIG_BYPASS=1
  # 然后重新执行操作，bypass 仅对当前 shell 会话生效
  # 所有 bypass 操作会被记录到审计日志

───────────────────────────────────────────────────────────────
请先完成安全流程，再继续配置变更。
""".strip()


# ──────────────────────────────────────────────
# 主逻辑
# ──────────────────────────────────────────────

def main():
    # 读取 hook 输入（Claude Code 通过 stdin 传入 JSON）
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # 无法解析则放行，不阻断正常工作流

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # bypass 模式
    if is_bypass_enabled():
        _log_bypass(tool_name, tool_input)
        sys.exit(0)

    blocked_path: str | None = None
    proposed_file: str | None = None

    if tool_name in ("Edit", "Write"):
        filepath = tool_input.get("file_path", "")
        if filepath and is_critical_path(filepath):
            blocked_path = filepath
            proposed_file = capture_proposed_content(tool_name, tool_input, filepath)

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if command:
            blocked_path = find_critical_bash_target(command)

    if blocked_path:
        print(build_block_message(blocked_path, tool_name, proposed_file))
        sys.exit(2)

    sys.exit(0)


def _log_bypass(tool_name: str, tool_input: dict):
    """记录 bypass 事件到审计日志"""
    import datetime
    log_dir = Path("~/.safeconfig/logs").expanduser()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"audit_{datetime.datetime.now().strftime('%Y%m')}.log"

    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": "SAFECONFIG_BYPASS",
        "user": os.getenv("USER") or f"uid_{os.getuid()}",
        "tool": tool_name,
        "target": tool_input.get("file_path") or tool_input.get("command", "")[:200],
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
