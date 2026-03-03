#!/usr/bin/env python3
"""
Config Guardian - Safe Configuration Management Script
Validates parameters, backs up configs, requires user confirmation
"""

import sys
import os
import json
import shutil
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Critical configuration files list
CRITICAL_CONFIGS = [
    "~/.openclaw/openclaw.json",
    "/etc/systemd/system/openclaw.service",
    "/etc/nginx/nginx.conf",
    "~/.ssh/config",
]

def backup_config(filepath):
    """Create config backup"""
    filepath = Path(filepath).expanduser()
    if not filepath.exists():
        return None
    
    backup_dir = Path("~/.config-backups").expanduser()
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{filepath.name}.{timestamp}.bak"
    
    shutil.copy2(filepath, backup_path)
    return backup_path

def validate_openclaw_param(param):
    """Validate openclaw parameter exists"""
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "start", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        help_text = result.stdout + result.stderr
        return param in help_text
    except Exception:
        return None  # Unable to verify

def validate_systemd_config(filepath):
    """Validate systemd config syntax"""
    try:
        result = subprocess.run(
            ["systemd-analyze", "verify", str(filepath)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def is_critical_config(filepath):
    """Check if file is a critical config"""
    filepath = Path(filepath).expanduser().resolve()
    for critical in CRITICAL_CONFIGS:
        critical_path = Path(critical).expanduser().resolve()
        if filepath == critical_path:
            return True
    return False

def generate_checklist(config_type, changes):
    """Generate safety checklist"""
    checklist = []
    
    if config_type == "openclaw.json":
        checklist.append("□ Check openclaw version compatibility")
        for change in changes:
            if "param" in change:
                valid = validate_openclaw_param(change["param"])
                if valid is False:
                    checklist.append(f"⚠️  Parameter '{change['param']}' may not exist")
                elif valid is True:
                    checklist.append(f"✅ Parameter '{change['param']}' validated")
    
    elif config_type == "systemd":
        checklist.append("□ Validate systemd config syntax")
        checklist.append("□ Confirm ExecStart parameter validity")
    
    checklist.append("□ Config backup created")
    checklist.append("□ User confirmation obtained")
    checklist.append("□ Service status verified after modification")
    
    return checklist

def main():
    parser = argparse.ArgumentParser(description="Config Guardian - Safe Configuration Management")
    parser.add_argument("--check", help="Check if file is critical config")
    parser.add_argument("--backup", help="Backup specified config file")
    parser.add_argument("--validate-systemd", help="Validate systemd config file")
    parser.add_argument("--type", choices=["openclaw.json", "systemd", "nginx", "ssh"], 
                        help="Config type")
    
    args = parser.parse_args()
    
    if args.check:
        filepath = Path(args.check).expanduser()
        is_critical = is_critical_config(filepath)
        print(f"File: {filepath}")
        print(f"Critical config: {'Yes' if is_critical else 'No'}")
        if is_critical:
            print("\n⚠️  This is a critical config file. Before modification:")
            print("  1. Validate parameter existence")
            print("  2. Create backup")
            print("  3. Get user confirmation")
        return 0 if not is_critical else 1
    
    if args.backup:
        filepath = Path(args.backup).expanduser()
        backup_path = backup_config(filepath)
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
            return 0
        else:
            print(f"⚠️  File doesn't exist, no backup needed: {filepath}")
            return 1
    
    if args.validate_systemd:
        valid, error = validate_systemd_config(args.validate_systemd)
        if valid:
            print("✅ systemd config validated")
            return 0
        else:
            print(f"❌ systemd config error: {error}")
            return 1
    
    # Default: show safety checklist template
    print("=" * 50)
    print("Config Guardian - Safety Checklist")
    print("=" * 50)
    print("\nCritical config files:")
    for cfg in CRITICAL_CONFIGS:
        print(f"  • {cfg}")
    print("\nRequired before modification:")
    print("  1. Verify parameter exists (--help)")
    print("  2. Create config backup")
    print("  3. Show changes to user")
    print("  4. Get explicit user confirmation")
    print("  5. Verify service status after modification")
    print("\nUsage:")
    print("  config-guardian --check <filepath>     # Check if critical")
    print("  config-guardian --backup <filepath>    # Backup config")
    print("  config-guardian --validate-systemd <file>  # Validate systemd")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
