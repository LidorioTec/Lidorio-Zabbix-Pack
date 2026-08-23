# LT Bareos

Monitoramento da suite de backup Bareos (Director, Storage Daemon,
File Daemon, catalog, jobs, pools) no padrao LIDORIO TECH.

## Versao
v0.2.0 - 24/08/2026

## Compatibilidade
- Zabbix Server 7.0 LTS (validado no 7.0.29)
- Coletor testado com Zabbix Agent 2 7.2.15 (backup01, Debian 13)
- Bareos 25.1.x com catalog PostgreSQL

## Pre-requisitos / Instalacao
1. Criar role somente leitura no PostgreSQL (zabbix_ro) com SELECT
   nas tabelas do catalog.
2. Instalar Scripts/Bareos/lt_bareos.py em /etc/zabbix/scripts/ (755).
3. Criar /etc/zabbix/scripts/lt_bareos.conf (640 root:zabbix) a partir
   de lt_bareos.conf.example. NUNCA commitar credenciais reais.
4. Instalar Scripts/Bareos/userparameter_lt_bareos.conf em
   /etc/zabbix/zabbix_agent2.d/ e reiniciar o agent.

## Heranca
Herda LT Linux Base. NAO vincule LT Linux Base diretamente em hosts
que recebem LT Bareos (erro "linked twice").

## Discovery Rules (2)
- Bareos clients discovery (bareos.clients.discovery, 1h)
- Bareos pools discovery (bareos.pools.discovery, 1h)

## Macros (8)
{$BAREOS.CLIENT.AGE.WARN}=7 | {$BAREOS.CLIENT.AGE.HIGH}=14 |
{$BAREOS.FULL.AGE.WARN}=7 | {$BAREOS.FULL.AGE.HIGH}=14 |
{$BAREOS.DIFF.AGE.WARN}=3 | {$BAREOS.INC.AGE.WARN}=2 |
{$BAREOS.SCRATCH.MIN.VOLUMES}=0 | {$BAREOS.SIZE.DROP.PCT}=50

## Triggers (severidade por nivel)
- Full FAILED = HIGH | Differential FAILED = AVERAGE | Incremental FAILED = WARNING
- Cliente sem backup > WARN/HIGH dias = AVERAGE/HIGH
- Director/SD DOWN = DISASTER | FD DOWN / catalog inacessivel = HIGH
- Queda abrupta de tamanho do Full = AVERAGE (continuidade;
  {$BAREOS.SIZE.DROP.PCT}=0 desativa em clientes pequenos)

## Troubleshooting
- -1 = nenhum job daquele nivel ainda (itens Numeric float).
- agegood 99999 = cliente nunca teve backup bem-sucedido ("unprotected").
- Erros de bsmtp/mailcommand nao alteram JobStatus de jobs concluidos;
  o coletor nao depende de mailcommand por design.
- Apos mudar prototypes, itens descobertos sincronizam na proxima
  execucao da LLD (ou reinicio do server/Execute now).

## Historico
- v0.2.0 (24/08/2026): primeira versao validada no Zabbix 7.0 LTS.
