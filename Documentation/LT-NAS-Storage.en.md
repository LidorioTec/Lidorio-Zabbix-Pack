# LT NAS Storage

NAS/Storage monitoring - LIDORIO TECH standard. Initial adapter:
OpenMediaVault (OMV 8.x) via read-only RPC REST API.

## Version
v0.3.0 - 2026-08-24

## Compatibility
- Zabbix Server 7.0 LTS (validated on 7.0.29)
- OpenMediaVault 8.5.6 on Debian 13 (storage01)
- Inherits LT Linux Base on Linux platforms

## Prerequisites / Installation
1. Install python3-requests on the monitored host.
2. Install Scripts/NAS/lt_omv.py into /etc/zabbix/scripts/ (755, root:root).
3. Create /etc/zabbix/scripts/lt_omv.conf (640 root:zabbix) from
   lt_omv.conf.example. NEVER commit real credentials.
4. Install Scripts/NAS/userparameter_lt_omv.conf into
   /etc/zabbix/zabbix_agent2.d/ and restart the agent.

## Inheritance
Inherits LT Linux Base. Do NOT link LT Linux Base directly on hosts
that receive LT NAS Storage ("linked twice" error).

## Architecture (adapter pattern)
LT NAS Storage
       |
       +-- OpenMediaVault (RPC REST via cookie)
       +-- (future) TrueNAS SCALE (REST API)
       +-- (future) Generic NAS (SNMP)

## Discovery rules (2)
- OMV filesystems discovery (1h) — filters mounted=true, non-swap, non-root
- OMV disks discovery (1h)

## Macros (4)
Filesystem usage thresholds (WARN/HIGH) and disk temperature thresholds
(WARN/HIGH). Setting to 0 disables the indicator.

## Triggers
- OMV API unreachable = HIGH
- Filesystem filling up / critically full = WARNING / HIGH
- Disk temperature above threshold = WARNING / HIGH
  (temperature=0 means sensor unavailable, no false positive)

## Troubleshooting
- Temperature 0: virtual disks (VirtualBox, VMware) do not expose SMART;
  on real hardware the value will be populated by OMV.
- 120s cache at /tmp/lt_omv_cache.json; rm -f to force refresh.
- Config permission must be 640 root:zabbix (not 600).

## Collection methods (adapters)
- v0.3.0: OpenMediaVault via RPC REST API (cookie), priority-1 method.
- SNMP is not used in this release: reserved for the "Generic Storage"
  adapter targeting physical appliances without proper APIs (Synology,
  QNAP, NetApp). Generic host MIBs are already covered by
  LT Linux Base via agent; do not duplicate.

## History
- v0.3.0 (2026-08-24): first adapter (OpenMediaVault) validated.

## Installation

### Prerequisites

- Zabbix Server 7.0 LTS
- OpenMediaVault 7.x (Debian-based)
- Zabbix Agent 2 on OMV host
- Python 3.8+ on OMV

### Procedure

#### 1. Install Zabbix Agent 2 on OMV

OMV is Debian-based, so use apt:

~~~bash
# Add official Zabbix repository
wget https://repo.zabbix.com/zabbix-release/7.0/zabbix-release_latest+debian12_all.deb
sudo dpkg -i zabbix-release_latest+debian12_all.deb
sudo apt update
sudo apt install -y zabbix-agent2

# Enable and start
sudo systemctl enable --now zabbix-agent2
~~~

#### 2. Install OMV collector

~~~bash
sudo mkdir -p /etc/zabbix/scripts

sudo wget -O /etc/zabbix/scripts/lt_omv.py \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/NAS/lt_omv.py
sudo chmod 755 /etc/zabbix/scripts/lt_omv.py

# Configuration (if OMV uses omv-confdbadm or local API)
sudo tee /etc/zabbix/scripts/lt_omv.conf > /dev/null << 'EOCONF'
omv_cli=/usr/sbin/omv-confdbadm
EOCONF
sudo chmod 640 /etc/zabbix/scripts/lt_omv.conf
sudo chown root:zabbix /etc/zabbix/scripts/lt_omv.conf

# UserParameter
sudo wget -O /etc/zabbix/zabbix_agent2.d/lt_omv.conf \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/NAS/userparameter_lt_omv.conf

sudo systemctl restart zabbix-agent2
~~~

#### 3. Test

~~~bash
sudo -u zabbix /etc/zabbix/scripts/lt_omv.py shares
# expected: list of shares

# from Zabbix server:
zabbix_get -s OMV_IP -k "omv.discover.shares"
~~~

#### 4. Import template and link

1. Data collection → Templates → Import → `Templates/NAS/LT_NAS_Storage.yaml`
2. Data collection → Hosts → [OMV host] → Link → `LT NAS Storage` → Update
3. Monitoring → Latest data → filter `omv`

## Troubleshooting

### "Permission denied" on omv-confdbadm
The collector needs root or sudo. Adjust the UserParameter to use
`sudo` (configure passwordless sudoers for the command).

### Item "Not supported"
Check UserParameter: `zabbix_agent2 -T | grep omv`; restart agent.
