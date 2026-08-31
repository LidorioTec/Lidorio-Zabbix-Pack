# LT Samba AD — LIDORIO TECH

Monitoramento moderno de Samba4 / Active Directory via LDAP read-only,
sem shell scripts, sem cron e sem sudo.

## Exclusividades LIDORIO TECH

Diferencial sobre templates legados (Galvy 2021, 4Linux 2016):

| Caracteristica | Legado | LT Samba AD |
|----------------|--------|-------------|
| Coleta | shell + samba-tool + cron + sudo | Python puro + LDAP read-only |
| Discovery de DCs | manual | automatico via DNS SRV |
| FSMO roles | nao | sim (5 roles mapeadas) |
| Tombstone lifetime | nao | sim (alerta proativo) |
| Password policy | nao | sim (compliance baseline) |
| Contas locked/expired | nao | sim |
| Functional level | nao | sim |

## Instalação

### Pré-requisitos

- Zabbix Server 7.0 LTS + Agent 2 no DC
- Samba AD DC (4.x+) ou Windows Server AD
- Python 3.8+ com ldap3 e dnspython
- Conta AD read-only para bind LDAP

### Procedimento

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

Instalar o coletor (auto-installer):

~~~bash
sudo ./install_lt_samba_ad.sh
sudo nano /etc/zabbix/scripts/lt_samba_ad.conf
~~~

### Criar conta read-only no AD (no DC)

~~~bash
samba-tool user create zabbix_ro 'SenhaForte123!'
~~~

### Testar

~~~bash
sudo -u zabbix python3 /etc/zabbix/scripts/lt_samba_ad.py ping
# esperado: 1
sudo -u zabbix python3 /etc/zabbix/scripts/lt_samba_ad.py discover_dcs
# esperado: {"data": [{"{#DC}": "dc01"}]}
sudo -u zabbix python3 /etc/zabbix/scripts/lt_samba_ad.py fsmo
# esperado: JSON com as 5 roles
~~~

### Importar template

1. Data collection → Templates → Import → `Templates/Samba/LT_Samba_AD.yaml`
2. Link ao host do DC → Update
3. Monitoring → Latest data → filtro `sambaad`

## Troubleshooting

### ping retorna 0
Verificar bind_dn/senha e URI LDAP. Testar manualmente:
`python3 -c "import ldap3; ..."` ou checar log em /var/log/zabbix/lt_samba_ad.log

### discover_dcs vazio
DNS SRV nao resolve: conferir /etc/resolv.conf do host (deve apontar
para o DNS do AD) e testar `host -t SRV _ldap._tcp.DOMINIO`.

### SELinux (Rocky/RHEL)
Conexoes LDAP de saida sao permitidas por padrao; se bloquear:
`setsebool -P zabbix_can_network 1`
