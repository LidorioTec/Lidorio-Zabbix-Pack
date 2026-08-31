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

## Instalação

### Pré-requisitos

- Zabbix Server 7.0 LTS
- RustFS (storage S3-compatible)
- Python 3.8+ com biblioteca `requests`
- Zabbix Agent 2 no host do RustFS

### Procedimento

#### 1. Instalar dependências (host do RustFS)

Debian/Ubuntu:

~~~bash
sudo apt update && sudo apt install -y python3 python3-pip
sudo pip3 install requests
~~~

RHEL/Rocky/Alma:

~~~bash
sudo dnf install -y python3 python3-pip
sudo pip3 install requests
~~~

#### 2. Instalar o coletor

~~~bash
sudo mkdir -p /etc/zabbix/scripts

# Baixar script principal
sudo wget -O /etc/zabbix/scripts/lt_rustfs.py \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/RustFS/lt_rustfs.py
sudo chmod 755 /etc/zabbix/scripts/lt_rustfs.py

# Criar arquivo de configuração
sudo tee /etc/zabbix/scripts/lt_rustfs.conf > /dev/null << 'EOCONF'
rustfs_url=http://localhost:9000
access_key=SUA_ACCESS_KEY_AQUI
secret_key=SUA_SECRET_KEY_AQUI
EOCONF

sudo chmod 640 /etc/zabbix/scripts/lt_rustfs.conf
sudo chown root:zabbix /etc/zabbix/scripts/lt_rustfs.conf

# Instalar UserParameter
sudo wget -O /etc/zabbix/zabbix_agent2.d/lt_rustfs.conf \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/RustFS/userparameter_lt_rustfs.conf

# Reiniciar agent
sudo systemctl restart zabbix-agent2
~~~

#### 3. Testar

~~~bash
# Testar script diretamente
sudo -u zabbix /etc/zabbix/scripts/lt_rustfs.py buckets
# esperado: lista de buckets

# Testar via Zabbix (do servidor Zabbix)
zabbix_get -s IP_DO_RUSTFS -k "rustfs.discover.buckets"
# esperado: JSON com lista de buckets
~~~

#### 4. Importar template e vincular ao host

1. Data collection → Templates → Import → `Templates/RustFS/LT_RustFS.yaml`
2. Data collection → Hosts → [host do RustFS] → Link → `LT RustFS` → Update
3. Monitoring → Latest data → filtro `rustfs`

## Troubleshooting

### "Permission denied" no script
Permissões do conf: `chown root:zabbix` + `chmod 640`

### "Connection refused" ao RustFS
Verificar se RustFS está rodando e acessível na URL configurada

### Item "Not supported"
Conferir UserParameter: `zabbix_agent2 -T | grep rustfs`; restart do agent
