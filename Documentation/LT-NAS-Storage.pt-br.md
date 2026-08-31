# LT NAS Storage

Monitoramento de NAS/Storage no padrao LIDORIO TECH. Adaptador inicial:
OpenMediaVault (OMV 8.x) via API RPC REST (read-only).

## Versao
v0.3.0 - 24/08/2026

## Compatibilidade
- Zabbix Server 7.0 LTS (validado no 7.0.29)
- OpenMediaVault 8.5.6 sobre Debian 13 (storage01)
- Herda LT Linux Base em plataformas Linux

## Pre-requisitos / Instalacao
1. Instalar python3-requests no host monitorado.
2. Instalar Scripts/NAS/lt_omv.py em /etc/zabbix/scripts/ (755, root:root).
3. Criar /etc/zabbix/scripts/lt_omv.conf (640 root:zabbix) a partir de
   lt_omv.conf.example. NUNCA commitar credenciais reais.
4. Instalar Scripts/NAS/userparameter_lt_omv.conf em
   /etc/zabbix/zabbix_agent2.d/ e reiniciar o agent.

## Heranca
Herda LT Linux Base. NAO vincule LT Linux Base diretamente em hosts
que recebem LT NAS Storage (erro "linked twice").

## Architecture Adapter
LT NAS Storage
       |
       +-- OpenMediaVault (RPC REST via cookie)
       +-- (futuro) TrueNAS SCALE (REST API)
       +-- (futuro) Generic NAS (SNMP)

## Discovery Rules (2)
- OMV filesystems discovery (omv.discover.filesystems, 1h)
  filtra: mounted=true, type != swap, _readonly=false
- OMV disks discovery (omv.discover.disks, 1h)

## Macros (4)
{$NAS.FS.PUSED.WARN}=80 | {$NAS.FS.PUSED.HIGH}=90 |
{$NAS.DISK.TEMP.WARN}=50 | {$NAS.DISK.TEMP.HIGH}=60

## Triggers
- OMV API unreachable = HIGH
- Filesystem filling up (>WARN%) = WARNING
- Filesystem critically full (>HIGH%) = HIGH
- Disk temperature > WARN/HIGH = WARNING/HIGH (0 = sem sensor, sem falso positivo)

## Troubleshooting
- Temperature 0: discos virtuais (VirtualBox, VMware) nao expoe SMART;
  em hardware real o valor sera preenchido via OMV.
- Cache de 120s em /tmp/lt_omv_cache.json; limpar com rm -f para
  forcar nova coleta apos mudancas.
- Permissao do .conf deve ser 640 root:zabbix (nao 600).

## Metodos de coleta (adapters)
- v0.3.0: OpenMediaVault via API RPC REST (cookie), metodo prioridade 1.
- SNMP nao e usado nesta versao: fica reservado ao adaptador
  "Generic Storage" para equipamentos fisicos sem API (Synology,
  QNAP, NetApp). MIBs genericas de host ja sao cobertas pelo
  LT Linux Base via agent; nao duplicar.

## Historico
- v0.3.0 (24/08/2026): primeiro adaptador (OpenMediaVault) validado.

## Instalação

### Pré-requisitos

- Zabbix Server 7.0 LTS
- OpenMediaVault 7.x (Debian-based)
- Zabbix Agent 2 no host OMV
- Python 3.8+ no OMV

### Procedimento

#### 1. Instalar Zabbix Agent 2 no OMV

O OMV é Debian-based, então use apt:

~~~bash
# Adicionar repositório oficial do Zabbix
wget https://repo.zabbix.com/zabbix-release/7.0/zabbix-release_latest+debian12_all.deb
sudo dpkg -i zabbix-release_latest+debian12_all.deb
sudo apt update
sudo apt install -y zabbix-agent2

# Habilitar e iniciar
sudo systemctl enable --now zabbix-agent2
~~~

#### 2. Instalar o coletor OMV

~~~bash
sudo mkdir -p /etc/zabbix/scripts

sudo wget -O /etc/zabbix/scripts/lt_omv.py \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/NAS/lt_omv.py
sudo chmod 755 /etc/zabbix/scripts/lt_omv.py

# Configuração (se o OMV usar omv-conf ou API local)
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

#### 3. Testar

~~~bash
sudo -u zabbix /etc/zabbix/scripts/lt_omv.py shares
# esperado: lista de shares

# do servidor Zabbix:
zabbix_get -s IP_DO_OMV -k "omv.discover.shares"
~~~

#### 4. Importar template e vincular

1. Data collection → Templates → Import → `Templates/NAS/LT_NAS_Storage.yaml`
2. Data collection → Hosts → [host OMV] → Link → `LT NAS Storage` → Update
3. Monitoring → Latest data → filtro `omv`

## Troubleshooting

### "Permission denied" no omv-confdbadm
O coletor precisa rodar como root ou com sudo. Ajuste o UserParameter
para usar `sudo` (configure sudoers sem senha para o comando).

### Item "Not supported"
Conferir UserParameter: `zabbix_agent2 -T | grep omv`; restart do agent.
