#!/bin/bash
# ============================================================================
# LIDORIO TECH - LT TrueNAS SNMP traps installer (server-side, multi-distro)
# Usage: sudo ./install_lt_truenas_traps.sh
# Note: Run on the ZABBIX SERVER (not on TrueNAS, which is agentless)
# ============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/lib_lt.sh"

echo "[LT] Installing TrueNAS SNMP trap pipeline on $(detect_family)..."

# 1. Install net-snmp + perl
echo "[LT] Installing net-snmp + net-snmp-perl..."
pkg_install net-snmp-utils net-snmp net-snmp-perl

# 2. Download official Zabbix trap receiver
mkdir -p /usr/lib/zabbix
wget -q -O /usr/lib/zabbix/zabbix_trap_receiver.pl \
  https://raw.githubusercontent.com/zabbix/zabbix/master/misc/snmptrap/zabbix_trap_receiver.pl
chmod 755 /usr/lib/zabbix/zabbix_trap_receiver.pl

# 3. Configure snmptrapd
cat > /etc/snmp/snmptrapd.conf << 'EOCONF'
authCommunity log,execute,net public
perl do "/usr/lib/zabbix/zabbix_trap_receiver.pl";
EOCONF

# 4. Create log directory
mkdir -p /var/log/snmptrap
touch /var/log/snmptrap/snmptrap.log
chown root:zabbix /var/log/snmptrap/snmptrap.log
chmod 644 /var/log/snmptrap/snmptrap.log

# 5. Enable snmptrapd
service_enable snmptrapd

# 6. Open port 162/udp in firewall
echo "[LT] Opening port 162/udp..."
open_port 162/udp

# 7. Configure Zabbix Server (SNMPTrapperFile + StartSNMPTrapper)
if ! grep -q "^StartSNMPTrapper=1" /etc/zabbix/zabbix_server.conf; then
    cat >> /etc/zabbix/zabbix_server.conf << 'EOCONF'

# SNMP Trapper (LT TrueNAS)
StartSNMPTrapper=1
SNMPTrapperFile=/var/log/snmptrap/snmptrap.log
EOCONF
    echo "[LT] Added SNMPTrapper config to zabbix_server.conf"
fi

# 8. Restart Zabbix Server
echo "[LT] Restarting zabbix-server..."
service_restart zabbix-server

# 9. SELinux warning
SEL=$(selinux_status)
if [ "$SEL" = "Enforcing" ]; then
    echo "[LT] WARNING: SELinux is Enforcing. You may need a custom module:"
    echo "     sudo grep snmptrap /var/log/audit/audit.log | audit2allow -M snmptrap"
    echo "     sudo semodule -i snmptrap.pp"
fi

echo "[LT] Trap pipeline installed! Remember to:"
echo "  1. Enable SNMP v2c on TrueNAS (Web UI)"
echo "  2. Import Templates/TrueNAS/LT_TrueNAS.yaml in Zabbix"
echo "  3. Test: snmptrap -v 2c -c public localhost '' 1.3.6.1.4.1.50536.2.1 ..."
