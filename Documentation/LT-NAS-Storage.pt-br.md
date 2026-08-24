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
