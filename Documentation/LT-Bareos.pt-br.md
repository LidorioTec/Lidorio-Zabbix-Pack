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

## Decisoes de design (vs. templates legados da comunidade)

O LT Bareos foi desenhado a partir da analise critica de implementacoes
historicas (2015-2018, Zabbix 2.4-3.4 / Bareos 15-17). As seguintes
decisoes de arquitetura sao diferenciais deliberados do projeto:

### Coleta nao-invasiva (read-only)
Templates legados dependem de hooks no `mailcommand` do `bareos-dir.conf`
e de `zabbix_sender` para enviar dados ao server. Isso acopla o
monitoramento ao ciclo de vida dos jobs e falha quando o mailer nao
esta disponivel. O LT Bareos consulta o catalog via SQL em modo
read-only (usuario `zabbix_ro` com SELECT), sem alterar nenhuma
configuracao do Bareos.

### Cache de dados (120s)
Todas as queries sao agrupadas em um unico lote a cada 120 segundos,
independente do numero de clients, pools ou itens ativos. Templates
legados disparavam queries por job ou por item, causando carga
desnecessaria no catalog em escala.

### LLD combinado com severidade dinamica por nivel
Templates antigos tinham LLD (descoberta de clients) **ou** severidade
por nivel de backup (Full/Diff/Inc), mas nunca ambos. O LT Bareos usa
trigger prototypes dentro da LLD para atribuir severidade adequada a
cada nivel: Full = HIGH, Differential = AVERAGE, Incremental = WARNING.

### Indicadores de continuidade
Alem do status do ultimo job, o template monitora:
- Idade do ultimo backup bem-sucedido por client (`agegood`)
- Queda abrupta de tamanho entre Fulls consecutivos (indicador de
  continuidade / possivel ransomware)
- Idade especifica por nivel (Full, Diff, Inc)

Esses indicadores detectam falhas de politica e comportamento anomalo
que um simples "ultimo job falhou?" nao captura.

### Semantica explicita de "sem dados"
- `-1`: nenhum job daquele nivel ainda (nao dispara trigger)
- `99999`: client nunca teve backup bem-sucedido (dispara "unprotected")

Templates legados frequentemente produziam falsos positivos ou buracos
de monitoramento nessas situacoes.

### Thresholds 100% via macros
Todas as 8 macros de threshold sao ajustaveis por host sem editar
nenhuma trigger. O valor `0` em macros especificas desliga o
correspondente indicador (ex.: `{$BAREOS.SIZE.DROP.PCT}=0` desativa
a detecao de queda de tamanho em clients pequenos/variaveis).

### Heranca e padronizacao
O LT Bareos herda o LT Linux Base, evitando duplicacao de itens de
SO/infraestrutura. Tags padronizadas (`component:*`, `service:bareos`)
permitem filtragem consistente em dashboards e acoes. Nomes de hosts
no Zabbix nao precisam ser iguais aos nomes de clients no Bareos (ao
contrario de algumas implementacoes legadas), gracas ao LLD.

## Historico
- v0.2.0 (24/08/2026): primeira versao validada no Zabbix 7.0 LTS.
