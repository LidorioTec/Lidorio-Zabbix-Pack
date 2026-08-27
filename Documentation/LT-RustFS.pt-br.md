# LT RustFS

Monitoramento de object storage S3-compativel RustFS no padrao LIDORIO TECH.

## Versao
v0.4.0 - 27/08/2026

## Compatibilidade
- Zabbix Server 7.0 LTS (validado no 7.0.30)
- RustFS 1.0.0-rc.3 (rustfs01, Debian 12)
- Cliente rc 0.1.31

## Pre-requisitos / Instalacao
1. Instalar o binario rc (cliente RustFS) no host monitorado.
2. Instalar Scripts/RustFS/lt_rustfs.py em /etc/zabbix/scripts/ (755).
3. Criar /etc/zabbix/scripts/lt_rustfs.conf (640 root:zabbix) a partir de
   lt_rustfs.conf.example. NUNCA commitar credenciais reais.
4. Configurar alias rc para o usuario zabbix (HOME=/var/lib/zabbix):
   sudo -u zabbix rc alias set rustfs_zabbix http://127.0.0.1:9000 USER PASS
5. Instalar Scripts/RustFS/userparameter_lt_rustfs.conf em
   /etc/zabbix/zabbix_agent2.d/ e reiniciar o agent.

## Metodos de coleta
- Health endpoints (/health, /minio/health/cluster) sem autenticacao.
- rc CLI (com alias) para buckets, objetos e bytes.
- du/df para capacity do volume de dados.
- Cache de 120s em /tmp/lt_rustfs.cache.json.

## Discovery Rules (1)
- RustFS buckets discovery (rustfs.discover.buckets, 1h)

## Macros (3)
{$RUSTFS.CAPACITY.WARN}=80 | {$RUSTFS.CAPACITY.HIGH}=90 |
{$RUSTFS.BUCKET.OBJECTS.MIN}=1

## Triggers
- RustFS unreachable = HIGH
- Cluster degraded = HIGH
- Data volume filling up (>WARN%) = WARNING
- Data volume critically full (>HIGH%) = HIGH
- Bucket empty (<MIN objects) = WARNING

## Limitacoes conhecidas
- RustFS 1.0.0-rc.3 nao expoe a rota admin.data-usage; o coletor usa
  rc ls --recursive --summarize (scan client-side) para bytes/objetos.

## Historico
- v0.4.0 (27/08/2026): primeiro release (single-node, buckets LLD).
