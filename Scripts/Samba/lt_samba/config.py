"""LT Samba FS - configuration validation.

Estrategia de fallback (LIDORIO TECH):
1. testparm -s  (sempre disponivel, rc=0 OK / rc=1 ERROR)
2. net conf list  (registry backend, raro)
3. unsupported_config_backend
"""

from . import utils


def validate_config():
    rc, out, err = utils.run_cmd(["testparm", "-s"])
    if rc == 127:
        rc2, _, _ = utils.run_cmd(["net", "conf", "list"])
        if rc2 == 0:
            return {"status": 0, "warnings": 0, "method": "net_conf"}
        return {"status": 1, "warnings": 0, "method": "unsupported"}
    warnings = err.count("WARNING") if err else 0
    return {"status": 0 if rc == 0 else 1, "warnings": warnings,
            "method": "testparm"}
