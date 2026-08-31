#!/bin/bash
# ============================================================================
# LIDORIO TECH - LT Bareos auto-installer (multi-distro)
# Usage: sudo ./install_lt_bareos.sh
# ============================================================================
set -e

# Load compatibility library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/lib_lt.sh"

echo "[LT] Installing LT Bareos collector on $(detect_family)..."

# 1. Install dependencies
echo "[LT] Installing postgresql client..."
pkg_install postgresql-client 2>/dev/null || pkg_install postgresql

# 2. Create scripts directory
mkdir -p /etc/zabbix/scripts

# 3. Install collector script
install_script "$SCRIPT_DIR/lt_bareos_lastbackup.py" /etc/zabbix/scripts/
chmod 755 /etc/zabbix/scripts/lt_bareos_lastbackup.py

# 4. Install UserParameter
AGENT_SVC=$(detect_agent_service)
if [ -z "$AGENT_SVC" ]; then
    echo "ERROR: no Zabbix agent service found" >&2
    exit 1
fi
AGENT_DIR="/etc/zabbix/${AGENT_SVC}.d"
mkdir -p "$AGENT_DIR"
install_script "$SCRIPT_DIR/userparameter_lt_bareos_lastbackup.conf" "$AGENT_DIR/" 644

# 5. Create config template (if not exists)
if [ ! -f /etc/zabbix/scripts/lt_bareos.conf ]; then
    cat > /etc/zabbix/scripts/lt_bareos.conf << 'EOCONF'
db_host=127.0.0.1
db_name=bareos
db_user=zabbix_ro
password=CHANGE_ME
EOCONF
    chmod 640 /etc/zabbix/scripts/lt_bareos.conf
    chown root:zabbix /etc/zabbix/scripts/lt_bareos.conf
    echo "[LT] Created /etc/zabbix/scripts/lt_bareos.conf (edit password!)"
fi

# 6. Restart agent
echo "[LT] Restarting $AGENT_SVC..."
service_restart "$AGENT_SVC"

echo "[LT] Installation complete! Remember to:"
echo "  1. Edit /etc/zabbix/scripts/lt_bareos.conf (password)"
echo "  2. Create zabbix_ro user in PostgreSQL (see docs)"
echo "  3. Import Templates/Bareos/LT_Bareos.yaml in Zabbix"
