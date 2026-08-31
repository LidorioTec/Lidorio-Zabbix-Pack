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

## Instalação

### Pré-requisitos

- Zabbix Server 7.0 LTS
- Bareos Director 23.x/24.x/25.x
- PostgreSQL (catálogo do Bareos)
- Python 3.8+ no host do Director

### Procedimento

#### 1. Preparar o banco (host do Director)

Debian/Ubuntu:

~~~bash
sudo apt update && sudo apt install -y postgresql-client
sudo -u postgres psql bareos << 'EOSQL'
CREATE USER zabbix_ro WITH PASSWORD 'SUA_SENHA_AQUI';
GRANT CONNECT ON DATABASE bareos TO zabbix_ro;
\c bareos
GRANT USAGE ON SCHEMA public TO zabbix_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO zabbix_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO zabbix_ro;
EOSQL
~~~

RHEL/Rocky/Alma:

~~~bash
sudo dnf install -y postgresql
# (mesmo bloco SQL do Debian acima)
~~~

#### 2. Instalar o coletor (host do Director)

Debian/Ubuntu:

~~~bash
sudo mkdir -p /etc/zabbix/scripts
sudo wget -O /etc/zabbix/scripts/lt_bareos_lastbackup.py \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/Bareos/lt_bareos_lastbackup.py
sudo chmod 755 /etc/zabbix/scripts/lt_bareos_lastbackup.py

sudo tee /etc/zabbix/scripts/lt_bareos.conf > /dev/null << 'EOCONF'
db_host=127.0.0.1
db_name=bareos
db_user=zabbix_ro
password=SUA_SENHA_AQUI
EOCONF
sudo chmod 640 /etc/zabbix/scripts/lt_bareos.conf
sudo chown root:zabbix /etc/zabbix/scripts/lt_bareos.conf

sudo wget -O /etc/zabbix/zabbix_agent2.d/lt_bareos_lastbackup.conf \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/Bareos/userparameter_lt_bareos_lastbackup.conf
sudo systemctl restart zabbix-agent2
~~~

RHEL/Rocky/Alma: mesmos comandos; reinicie com
`sudo systemctl restart zabbix-agent2 || sudo systemctl restart zabbix-agent`

#### 3. Testar

~~~bash
sudo -u zabbix /etc/zabbix/scripts/lt_bareos_lastbackup.py "notebook-01-fd"
# esperado: timestamp Unix

# do servidor Zabbix:
zabbix_get -s IP_DO_BAREOS -k "bareos.client.last.successful.backup[notebook-01-fd]"
~~~

#### 4. Importar template e vincular ao host

1. Data collection → Templates → Import → `Templates/Bareos/LT_Bareos.yaml`
2. Data collection → Hosts → [host do Director] → Link → `LT Bareos` → Update
3. Monitoring → Latest data → filtro `last successful backup`

## Troubleshooting

### "Permission denied" no script
Permissões do conf: `chown root:zabbix` + `chmod 640`.

### "Connection refused" no PostgreSQL
Garantir `listen_addresses = 'localhost'` e linha
`host bareos zabbix_ro 127.0.0.1/32 md5` no pg_hba.conf; restart postgresql.

### Item "Not supported"
Conferir UserParameter: `zabbix_agent2 -T | grep bareos`; restart do agent.
