"""LT Samba FS - shared utilities (LIDORIO TECH)."""

import os
import re
import subprocess


def run_cmd(args, timeout=10):
    """Executa comando SEM shell (seguro). Retorna (rc, stdout, stderr)."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", f"command not found: {args[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout: {args[0]}"
    except Exception as e:
        return 126, "", str(e)


def proc_count(name):
    """Conta processos via /proc/*/comm (pure Python, sem pgrep/ps)."""
    count = 0
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/comm") as f:
                if f.read().strip() == name:
                    count += 1
        except (OSError, IOError):
            continue
    return count


def parse_samba_version(text):
    """'Version 4.15.13-Debian' -> '4.15.13'."""
    m = re.search(r"Version\s+(\d+\.\d+\.\d+)", text)
    return m.group(1) if m else "unknown"
