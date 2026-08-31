#!/bin/bash
# ============================================================================
# LIDORIO TECH - LT RustFS auto-installer (multi-distro)
# Usage: sudo ./install_lt_rustfs.sh
# ============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/lib_lt.sh"

echo "[LT] Installing LT RustFS collector on $(detect_family)..."

# 1. Install dependencies (python3 + requests)
echo "[LT] Installing python3 + requests..."
pkg_install python3 python3-pip
pip3 install requests 2>/dev/null || pip3 install --break-system-packages requests

# 2. Create scripts directory
mkdir -p /etc/zabbix/scripts

# 3. Install collector script
install_script "$SCRIPT_DIR/lt_rustfs.py" /etc/zabbix/scripts/
chmod 755 /etc/zabbix/scripts/lt_rustfs.py

# 4. Install UserParameter
AGENT_SVC=$(detect_agent_service)
if [ -z "$AGENT_SVC" ]; then
    echo "ERROR: no Zabbix agent service found" >&2
    exit 1
fi
AGENT_DIR="/etc/zabbix/${AGENT_SVC}.d"
mkdir -p "$AGENT_DIR"
install_script "$SCRIPT_DIR/userparameter_lt_rustfs.conf" "$AGENT_DIR/" 644

# 5. Create config template (if not exists)
if [ ! -f /etc/zabbix/scripts/lt_rustfs.conf ]; then
    cat > /etc/zabbix/scripts/lt_rustfs.conf << 'EOCONF'
rustfs_url=http://localhost:9000
access_key=CHANGE_ME
secret_key=CHANGE_ME
EOCONF
    chmod 640 /etc/zabbix/scripts/lt_rustfs.conf
    chown root:zabbix /etc/zabbix/scripts/lt_rustfs.conf
    echo "[LT] Created /etc/zabbix/scripts/lt_rustfs.conf (edit credentials!)"
fi

# 6. Restart agent
echo "[LT] Restarting $AGENT_SVC..."
service_restart "$AGENT_SVC"

echo "[LT] Installation complete! Remember to:"
echo "  1. Edit /etc/zabbix/scripts/lt_rustfs.conf (credentials)"
echo "  2. Import Templates/RustFS/LT_RustFS.yaml in Zabbix"
