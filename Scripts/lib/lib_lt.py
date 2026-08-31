# ============================================================================
# LIDORIO TECH - Multi-distro Python compatibility library
# Version: 1.0.0 (v0.7.0)
# Purpose: Uniform config loading, logging, and OS detection for collectors
# Usage: import sys; sys.path.insert(0, "/etc/zabbix/lib"); import lib_lt
# ============================================================================
import os, sys, logging

# ----------------------------------------------------------------------------
# OS detection
# ----------------------------------------------------------------------------
def detect_family():
    """Returns: debian | redhat | arch | unknown"""
    try:
        with open("/etc/os-release") as f:
            data = dict(line.strip().split("=", 1)
                       for line in f if "=" in line)
        os_id = data.get("ID", "").strip('"')
        if os_id in ("debian", "ubuntu", "linuxmint", "pop"):
            return "debian"
        if os_id in ("rhel", "rocky", "alma", "fedora", "centos", "ol"):
            return "redhat"
        if os_id in ("arch", "manjaro"):
            return "arch"
    except Exception:
        pass
    return "unknown"

# ----------------------------------------------------------------------------
# Config loading (INI-style: key=value)
# ----------------------------------------------------------------------------
def load_config(path, defaults=None):
    """
    Load key=value config file. Returns dict merged with defaults.
    Missing file -> returns defaults (no error, graceful).
    """
    cfg = dict(defaults) if defaults else {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    except Exception as e:
        log("WARN", f"config read error: {e}")
    return cfg

# ----------------------------------------------------------------------------
# Standard paths (OS-aware)
# ----------------------------------------------------------------------------
def get_config_dir():
    return "/etc/zabbix/scripts"

def get_log_path(name):
    """Returns /var/log/zabbix/lt_<name>.log (Linux) or /tmp (fallback)"""
    log_dir = "/var/log/zabbix"
    if os.path.isdir(log_dir):
        return f"{log_dir}/lt_{name}.log"
    return f"/tmp/lt_{name}.log"

# ----------------------------------------------------------------------------
# Standard logger
# ----------------------------------------------------------------------------
_LOGGERS = {}

def get_logger(name):
    """Get/create a logger that writes to the standard log path."""
    if name in _LOGGERS:
        return _LOGGERS[name]
    logger = logging.getLogger(f"lt.{name}")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        try:
            fh = logging.FileHandler(get_log_path(name))
            fh.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(fh)
        except Exception:
            logger.addHandler(logging.StreamHandler())
    _LOGGERS[name] = logger
    return logger

def log(level, msg, name="common"):
    """Quick log: lib_lt.log("INFO", "message", name="bareos")"""
    lvl = getattr(logging, level.upper(), logging.INFO)
    get_logger(name).log(lvl, msg)

# ----------------------------------------------------------------------------
# Graceful exit helper for Zabbix items
# ----------------------------------------------------------------------------
def emit(value, exit_code=0):
    """Print value for Zabbix and exit. Use in main()."""
    print(value)
    sys.exit(exit_code)
