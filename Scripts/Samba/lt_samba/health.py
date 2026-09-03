"""LT Samba FS - service health com deteccao dinamica.

Nem todo servidor tem nmbd/winbind: reportamos estado real (1/0)
e o template decide o que eh obrigatorio (so smbd tem trigger).
"""

from . import utils

# logical service -> nome do processo em /proc
SERVICES = {
    "smbd": "smbd",
    "nmbd": "nmbd",
    "winbind": "winbindd",
}


def service_running(service):
    proc = SERVICES.get(service)
    if not proc:
        return -1
    return 1 if utils.proc_count(proc) > 0 else 0


def smbd_processes():
    return utils.proc_count("smbd")


def samba_version():
    rc, out, err = utils.run_cmd(["smbd", "--version"])
    if rc != 0:
        return "unknown"
    return utils.parse_samba_version(out + err)


def collect_health():
    return {
        "smbd": service_running("smbd"),
        "nmbd": service_running("nmbd"),
        "winbind": service_running("winbind"),
        "smbd_processes": smbd_processes(),
        "version": samba_version(),
    }
