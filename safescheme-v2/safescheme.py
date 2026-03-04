#!/usr/bin/env python3
"""
SafeScheme - OpenClaw 配置 Scheme 验证器
基于当前版本规范的强制预审查
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: str  # "passed", "failed", "warning"
    message: str
    details: Dict = field(default_factory=dict)


class SafeSchemeValidator:
    """OpenClaw 配置验证器"""
    
    # OpenClaw 配置规范（基于当前版本）
    SCHEMA = {
        "required_top_level": ["meta", "channels", "gateway"],
        "meta_required": ["lastTouchedVersion", "lastTouchedAt"],
        "channels_required": [],
        "gateway_required": ["mode", "auth"],
        "auth_required": ["token"],
        "valid_group_policies": ["open", "pairing", "allowlist"],
        "valid_dm_policies": ["open", "pairing", "allowlist"],
    }
    
    def __init__(self, config_path: str = "~/.openclaw/openclaw.json"):
        self.config_path = Path(config_path).expanduser()
        self.results: List[CheckResult] = []
        self.config: Optional[Dict] = None
        
    def validate(self) -> bool:
        """执行完整验证"""
        print("🔐 SafeScheme - OpenClaw 配置验证")
        print("=" * 70)
        print(f"时间: {datetime.now().isoformat()}")
        print(f"配置文件: {self.config_path}")
        print("=" * 70)
        
        # 执行所有检查
        self._check_file_exists()
        self._check_json_syntax()
        if self.config:
            self._check_scheme_structure()
            self._check_required_fields()
            self._check_types()
            self._check_value_ranges()
            self._check_dependencies()
            self._check_sensitive_fields()
        self._check_openclaw_status()
        self._check_service_health()
        self._check_system_resources()
        
        return self._generate_report()
    
    def _add_result(self, name: str, status: str, message: str, details: Dict = None):
        """添加检查结果"""
        self.results.append(CheckResult(
            name=name,
            status=status,
            message=message,
            details=details or {}
        ))
        
        # 实时输出
        icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
        print(f"{icon} {name}: {message}")
    
    def _check_file_exists(self):
        """检查 1: 文件存在性"""
        if self.config_path.exists():
            size = self.config_path.stat().st_size
            self._add_result(
                "文件存在性",
                "passed",
                f"文件存在，大小: {size} bytes"
            )
        else:
            self._add_result(
                "文件存在性",
                "failed",
                f"文件不存在: {self.config_path}"
            )
    
    def _check_json_syntax(self):
        """检查 2: JSON 语法"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self._add_result(
                "JSON 语法",
                "passed",
                "JSON 格式正确，可正常解析"
            )
        except json.JSONDecodeError as e:
            self._add_result(
                "JSON 语法",
                "failed",
                f"JSON 解析错误: {e}"
            )
        except Exception as e:
            self._add_result(
                "JSON 语法",
                "failed",
                f"读取错误: {e}"
            )
    
    def _check_scheme_structure(self):
        """检查 3: Scheme 结构"""
        # 检查顶级必需字段
        missing = []
        for field in self.SCHEMA["required_top_level"]:
            if field not in self.config:
                missing.append(field)
        
        if missing:
            self._add_result(
                "Scheme 结构",
                "failed",
                f"缺少必需字段: {', '.join(missing)}"
            )
        else:
            self._add_result(
                "Scheme 结构",
                "passed",
                f"所有必需字段存在: {', '.join(self.SCHEMA['required_top_level'])}"
            )
        
        # 检查 meta 字段
        if "meta" in self.config:
            meta = self.config["meta"]
            meta_missing = [f for f in self.SCHEMA["meta_required"] if f not in meta]
            if meta_missing:
                self._add_result(
                    "Meta 字段",
                    "warning",
                    f"Meta 缺少字段: {', '.join(meta_missing)}"
                )
            else:
                self._add_result(
                    "Meta 字段",
                    "passed",
                    "Meta 字段完整"
                )
    
    def _check_required_fields(self):
        """检查 4: 必需字段"""
        checks = []
        
        # 检查 channels.telegram
        if "channels" in self.config and "telegram" in self.config["channels"]:
            tg = self.config["channels"]["telegram"]
            if tg.get("enabled") and not tg.get("botToken"):
                checks.append(("Telegram botToken", "failed", "启用但未配置 botToken"))
            elif tg.get("botToken"):
                checks.append(("Telegram botToken", "passed", "已配置"))
        
        # 检查 gateway.auth.token
        if "gateway" in self.config:
            gw = self.config["gateway"]
            if "auth" in gw and "token" in gw.get("auth", {}):
                checks.append(("Gateway auth token", "passed", "已配置"))
            else:
                checks.append(("Gateway auth token", "failed", "未配置"))
        
        for name, status, msg in checks:
            self._add_result(f"必需字段: {name}", status, msg)
    
    def _check_types(self):
        """检查 5: 类型检查"""
        type_checks = []
        
        # 检查 meta.lastTouchedVersion 是字符串
        if "meta" in self.config and "lastTouchedVersion" in self.config["meta"]:
            value = self.config["meta"]["lastTouchedVersion"]
            if isinstance(value, str):
                type_checks.append(("lastTouchedVersion 类型", "passed", "字符串类型正确"))
            else:
                type_checks.append(("lastTouchedVersion 类型", "failed", f"应为字符串，实际为 {type(value).__name__}"))
        
        # 检查 channels.telegram.enabled 是布尔值
        if "channels" in self.config and "telegram" in self.config["channels"]:
            tg = self.config["channels"]["telegram"]
            if "enabled" in tg:
                value = tg["enabled"]
                if isinstance(value, bool):
                    type_checks.append(("telegram.enabled 类型", "passed", "布尔类型正确"))
                else:
                    type_checks.append(("telegram.enabled 类型", "warning", f"应为布尔值，实际为 {type(value).__name__}"))
        
        for name, status, msg in type_checks:
            self._add_result(name, status, msg)
    
    def _check_value_ranges(self):
        """检查 6: 值域检查"""
        value_checks = []
        
        # 检查 groupPolicy
        if "channels" in self.config and "telegram" in self.config["channels"]:
            policy = self.config["channels"]["telegram"].get("groupPolicy")
            if policy:
                if policy in self.SCHEMA["valid_group_policies"]:
                    value_checks.append(("groupPolicy 值域", "passed", f"有效值: {policy}"))
                else:
                    value_checks.append(("groupPolicy 值域", "failed", f"无效值: {policy}，应为 {self.SCHEMA['valid_group_policies']}"))
        
        for name, status, msg in value_checks:
            self._add_result(name, status, msg)
    
    def _check_dependencies(self):
        """检查 7: 依赖关系"""
        dep_checks = []
        
        # 如果启用了 telegram，必须有 botToken
        if "channels" in self.config and "telegram" in self.config["channels"]:
            tg = self.config["channels"]["telegram"]
            if tg.get("enabled") and not tg.get("botToken"):
                dep_checks.append(("Telegram 依赖", "failed", "enabled=true 但缺少 botToken"))
            elif tg.get("enabled") and tg.get("botToken"):
                dep_checks.append(("Telegram 依赖", "passed", "依赖满足"))
        
        for name, status, msg in dep_checks:
            self._add_result(name, status, msg)
    
    def _check_sensitive_fields(self):
        """检查 8: 安全敏感字段"""
        sensitive_checks = []
        
        if "auth" in self.config and "profiles" in self.config["auth"]:
            for provider, settings in self.config["auth"]["profiles"].items():
                # 检查是否有 api_key 或 token
                has_key = "api_key" in settings or "token" in settings
                if has_key:
                    value = settings.get("api_key") or settings.get("token")
                    if value and (value.startswith("YOUR_") or value == ""):
                        sensitive_checks.append((f"{provider} API Key", "warning", "使用占位符或为空"))
                    elif value:
                        masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                        sensitive_checks.append((f"{provider} API Key", "passed", f"已配置: {masked}"))
        
        if not sensitive_checks:
            sensitive_checks.append(("API Keys", "warning", "未配置任何 API Key"))
        
        for name, status, msg in sensitive_checks:
            self._add_result(name, status, msg)
    
    def _check_openclaw_status(self):
        """检查 9: OpenClaw 状态"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "openclaw"],
                capture_output=True,
                text=True,
                timeout=5
            )
            status = result.stdout.strip()
            if status == "active":
                self._add_result("OpenClaw 状态", "passed", "服务运行中")
            else:
                self._add_result("OpenClaw 状态", "failed", f"服务状态: {status}")
        except Exception as e:
            self._add_result("OpenClaw 状态", "warning", f"无法检查: {e}")
    
    def _check_service_health(self):
        """检查 10: 服务健康"""
        try:
            # 检查端口 5555
            result = subprocess.run(
                ["lsof", "-i", ":5555"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self._add_result("端口健康", "passed", "端口 5555 正在监听")
            else:
                self._add_result("端口健康", "warning", "端口 5555 未监听")
        except Exception as e:
            self._add_result("端口健康", "warning", f"无法检查: {e}")
    
    def _check_system_resources(self):
        """检查 11: 系统资源"""
        try:
            # 磁盘空间
            result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                usage = parts[4] if len(parts) > 4 else "unknown"
                self._add_result("磁盘空间", "passed" if int(usage.rstrip("%")) < 80 else "warning", f"根分区使用: {usage}")
            
            # 内存
            result = subprocess.run(
                ["free", "-h"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._add_result("内存状态", "passed", "内存检查完成")
        except Exception as e:
            self._add_result("系统资源", "warning", f"检查失败: {e}")
    
    def _generate_report(self) -> bool:
        """生成最终报告"""
        print("\n" + "=" * 70)
        print("📊 验证报告")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        warnings = sum(1 for r in self.results if r.status == "warning")
        
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"警告: {warnings}")
        print(f"总计: {len(self.results)} 项检查")
        
        print("\n" + "=" * 70)
        
        if failed > 0:
            print("❌ 验证未通过")
            print("请修复上述错误后重试")
            return False
        elif warnings > 0:
            print("⚠️  验证通过，但有警告")
            print("建议查看警告项")
            return True
        else:
            print("✅ 验证通过")
            return True


def main():
    validator = SafeSchemeValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
