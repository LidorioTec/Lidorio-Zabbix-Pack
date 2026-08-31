# LT Samba AD — LIDORIO TECH

Modern Samba4 / Active Directory monitoring via read-only LDAP,
no shell scripts, no cron, no sudo.

## LIDORIO TECH exclusives

Differential over legacy templates (Galvy 2021, 4Linux 2016):

| Feature | Legacy | LT Samba AD |
|---------|--------|-------------|
| Collection | shell + samba-tool + cron + sudo | Pure Python + read-only LDAP |
| DC discovery | manual | automatic via DNS SRV |
| FSMO roles | no | yes (5 roles mapped) |
| Tombstone lifetime | no | yes (proactive alert) |
| Password policy | no | yes (baseline compliance) |
| Locked/expired accounts | no | yes |
| Functional level | no | yes |

## Installation

### Prerequisites

- Zabbix Server 7.0 LTS + Agent 2 on the DC
- Samba AD DC (4.x+) or Windows Server AD
- Python 3.8+ with ldap3 and dnspython
- Read-only AD account for LDAP bind

### Procedure

Debian/Ubuntu:

~~~bash
sudo apt update && sudo apt install -y python3 python3-pip
sudo pip3 install ldap3 dnspython
~~~

RHEL/Rocky/Alma:

~~~bash
sudo dnf install -y python3 python3-pip
sudo pip3 install ldap3 dnspython
~~~

Install the collector (auto-installer):

~~~bash
sudo ./install_lt_samba_ad.sh
sudo nano /etc/zabbix/scripts/lt_samba_ad.conf
~~~

### Create read-only AD account (on the DC)

~~~bash
samba-tool user create zabbix_ro 'StrongPass123!'
~~~

### Test

~~~bash
sudo -u zabbix python3 /etc/zabbix/scripts/lt_samba_ad.py ping
# expected: 1
sudo -u zabbix python3 /etc/zabbix/scripts/lt_samba_ad.py discover_dcs
# expected: {"data": [{"{#DC}": "dc01"}]}
sudo -u zabbix python3 /etc/zabbix/scripts/lt_samba_ad.py fsmo
# expected: JSON with the 5 roles
~~~

### Import template

1. Data collection → Templates → Import → `Templates/Samba/LT_Samba_AD.yaml`
2. Link to the DC host → Update
3. Monitoring → Latest data → filter `sambaad`

## Troubleshooting

### ping returns 0
Check bind_dn/password and LDAP URI. Logs at /var/log/zabbix/lt_samba_ad.log

### discover_dcs empty
DNS SRV not resolving: check /etc/resolv.conf (must point to AD DNS)
and test `host -t SRV _ldap._tcp.DOMAIN`.

### SELinux (Rocky/RHEL)
Outbound LDAP is allowed by default; if blocked:
`setsebool -P zabbix_can_network 1`
