# LT TrueNAS

TrueNAS SCALE 25.10+ monitoring - LIDORIO TECH standard.

## Version
v0.5.0 - 2026-08-28

## Compatibility
- Zabbix Server 7.0 LTS (validated on 7.0.30)
- **TrueNAS SCALE 25.10.6** (OIDs specific to this version)

## Advantages over official Zabbix template

| Feature | Official 7.4 | **LT TrueNAS** |
|---------|--------------|----------------|
| OIDs for 25.10 | ❌ Broken | ✅ Validated on 25.10.6 |
| Capacity forecast | ❌ | ✅ `forecast()` (days to full) |
| ARC hit ratio trigger | ❌ | ✅ <80% = memory pressure |
| Agentless | ✅ SNMP | ✅ Pure SNMP (no Docker) |
| Correct datasets MIB | ❌ Swapped w/ zvols | ✅ `.1.6.1.1` (25.10) |

## Critical MIB changes in 25.10

iXsystems swapped several OIDs between datasets and zvols in version 25.10:

| Feature | Old OID (≤25.04) | Real OID (25.10+) |
|---------|-----------------|--------------------|
| Datasets | `.50536.1.2.1.1` | **`.50536.1.6.1.1`** |
| Zvols | `.50536.1.3.1.1` | **`.50536.1.2.1.1`** |
| L2ARC | `.50536.1.5.x` | **`.50536.1.4.x`** |
| ZIL | `.50536.1.6.x` | **`.50536.1.5.x`** |

## Prerequisites / Installation

1. Enable SNMP on TrueNAS: **Services → SNMP → Enable** (v2c, community `public` for lab)
2. Import `Templates/TrueNAS/LT_TrueNAS.yaml` into Zabbix
3. Link to host (SNMP v2c, community `public`)
4. Wait ~1h for LLDs to run

## Key macros
Pool/dataset capacity thresholds, ARC hit ratio, snapshot age.

## LLDs (2 rules)
- **ZFS pools discovery** (OID `.1.1.1.1.2`) → health, IOPS, bytes
- **ZFS datasets discovery** (OID `.1.6.1.1.2`, 25.10+) → used/avail/forecast

## Triggers (main)
- Pool not ONLINE = **HIGH**
- Dataset >80% = WARNING / >90% = AVERAGE
- Dataset full in <30 days = WARNING
- ARC hit ratio <80% = WARNING
- ICMP down / SNMP unavailable = HIGH/WARNING

## Validation
Tested on:
- `truenas01` (192.168.2.217) — TrueNAS SCALE 25.10.6
- Pool `tank` (MIRROR) with dataset `tank/backup`
- Zabbix Server 7.0.30 LTS

## Validation note (v0.6.0)
- Scrub: TRUENAS-MIB 25.10 does NOT expose a last-scrub OID (verified via
  snmpwalk and the official template). Scrub monitoring lands in v0.6.1 via
  SNMP traps (.1.3.6.1.4.1.50536.2) with snmptrapd on zabbix1.
- Disk temperature: VMs without sensors report 0 C; triggers only fire on
  HIGH temperature (no false positives).

## Installation

### Prerequisites

- Zabbix Server 7.0 LTS
- TrueNAS SCALE 25.10+
- SNMP enabled on TrueNAS
- `net-snmp-utils` and `net-snmp-perl` on Zabbix server

### Procedure

#### 1. Enable SNMP on TrueNAS (Web UI)

1. Access TrueNAS web interface
2. System → Services → SNMP → Enable
3. Configure:
   - SNMP v2c
   - Community: `public` (or your preference)
   - Log level: 3 (warnings)

#### 2. Configure traps on Zabbix server

~~~bash
# Install dependencies
sudo dnf install -y net-snmp-utils net-snmp-perl

# Create scripts directory
sudo mkdir -p /usr/lib/zabbix

# Download official Zabbix receiver
sudo wget -O /usr/lib/zabbix/zabbix_trap_receiver.pl \
  https://raw.githubusercontent.com/zabbix/zabbix/master/misc/snmptrap/zabbix_trap_receiver.pl

# Configure snmptrapd
sudo tee /etc/snmp/snmptrapd.conf > /dev/null << 'EOCONF'
authCommunity log,execute,net public
perl do "/usr/lib/zabbix/zabbix_trap_receiver.pl";
EOCONF

# Create log directory
sudo mkdir -p /var/log/snmptrap
sudo touch /var/log/snmptrap/snmptrap.log
sudo chown root:zabbix /var/log/snmptrap/snmptrap.log
sudo chmod 644 /var/log/snmptrap/snmptrap.log

# Enable and start snmptrapd
sudo systemctl enable --now snmptrapd

# Open port in firewalld
sudo firewall-cmd --add-port=162/udp --permanent
sudo firewall-cmd --reload
~~~

#### 3. Configure Zabbix Server to read traps

Edit `/etc/zabbix/zabbix_server.conf`:

~~~bash
sudo tee -a /etc/zabbix/zabbix_server.conf > /dev/null << 'EOCONF'

# SNMP Trapper
StartSNMPTrapper=1
SNMPTrapperFile=/var/log/snmptrap/snmptrap.log
EOCONF

sudo systemctl restart zabbix-server
~~~

#### 4. Import template and link host

1. Data collection → Templates → Import → `Templates/TrueNAS/LT_TrueNAS.yaml`
2. Data collection → Hosts → [TrueNAS host] → Link → `LT TrueNAS` → Update
3. Configure SNMP on host:
   - SNMP version: 2
   - Community: `public`
4. Monitoring → Latest data → filter `truenas`

#### 5. Test traps

On Zabbix server, send test trap:

~~~bash
snmptrap -v 2c -c public localhost "" 1.3.6.1.4.1.50536.2.1 \
  1.3.6.1.4.1.50536.2.1.1 s "Test trap"
~~~

Check Monitoring → Problems: should show "TrueNAS: SNMP trap received"

## Troubleshooting

### Traps not reaching Zabbix
Check firewalld: `sudo firewall-cmd --list-ports` (should include 162/udp)

### SELinux blocking traps
Check: `sudo getenforce`
If `Enforcing`, create module:

~~~bash
sudo grep snmptrap /var/log/audit/audit.log | audit2allow -M snmptrap
sudo semodule -i snmptrap.pp
~~~

### Perl script not writing to log
Check: `sudo tail -f /var/log/snmptrap/snmptrap.log` while sending trap
