#!/bin/bash
# ============================================================================
# LIDORIO TECH - LT Samba AD auto-installer (multi-distro)
# Usage: sudo ./install_lt_samba_ad.sh
# ============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/lib_lt.sh"

echo "[LT] Installing LT Samba AD collector on $(detect_family)..."

# 1. Python deps (ldap3 + dnspython, ambos pure-python)
echo "[LT] Installing python3 + ldap3 + dnspython..."
pkg_install python3 python3-pip
pip3 install ldap3 dnspython 2>/dev/null \
  || pip3 install --break-system-packages ldap3 dnspython

# 2. Scripts + lib
mkdir -p /etc/zabbix/scripts /etc/zabbix/lib
install_script "$SCRIPT_DIR/../lib/lib_lt.py" /etc/zabbix/lib/lib_lt.py 644
install_script "$SCRIPT_DIR/lt_samba_ad.py" /etc/zabbix/scripts/ 755

# 3. Config (somente se nao existir)
if [ ! -f /etc/zabbix/scripts/lt_samba_ad.conf ]; then
    install_script "$SCRIPT_DIR/lt_samba_ad.conf.example" \
        /etc/zabbix/scripts/lt_samba_ad.conf 640
    echo "[LT] Created /etc/zabbix/scripts/lt_samba_ad.conf (edit credentials!)"
fi

# 4. UserParameter
AGENT_SVC=$(detect_agent_service)
if [ -z "$AGENT_SVC" ]; then
    echo "ERROR: no Zabbix agent service found" >&2
    exit 1
fi
AGENT_DIR="/etc/zabbix/${AGENT_SVC}.d"
mkdir -p "$AGENT_DIR"
install_script "$SCRIPT_DIR/userparameter_lt_samba_ad.conf" "$AGENT_DIR/" 644

# 5. Restart agent
echo "[LT] Restarting $AGENT_SVC..."
service_restart "$AGENT_SVC"

echo "[LT] Installation complete! Remember to:"
echo "  1. Edit /etc/zabbix/scripts/lt_samba_ad.conf (domain + read-only bind)"
echo "  2. Import Templates/Samba/LT_Samba_AD.yaml in Zabbix"
