# LT TrueNAS

Monitoramento do TrueNAS SCALE 25.10+ no padrão LIDORIO TECH.

## Versão
v0.5.0 - 2026-08-28

## Compatibilidade
- Zabbix Server 7.0 LTS (validado no 7.0.30)
- **TrueNAS SCALE 25.10.6** (OIDs específicos desta versão)

## Diferenciais sobre o template oficial do Zabbix

| Recurso | Template oficial 7.4 | **LT TrueNAS** |
|---------|---------------------|----------------|
| OIDs 25.10 | ❌ Quebrados | ✅ Validados na 25.10.6 |
| Projeção de esgotamento | ❌ | ✅ `forecast()` (dias p/ encher) |
| Trigger ARC hit ratio | ❌ | ✅ <80% = memória sob pressão |
| Agentless | ✅ SNMP | ✅ SNMP puro (sem Docker) |
| MIB datasets correta | ❌ Trocou com zvols | ✅ `.1.6.1.1` (25.10) |

## Mudanças críticas da MIB 25.10

A iXsystems trocou vários OIDs entre datasets e zvols na versão 25.10:

| Feature | OID oficial (≤25.04) | OID real (25.10+) |
|---------|---------------------|-------------------|
| Datasets | `.50536.1.2.1.1` | **`.50536.1.6.1.1`** |
| Zvols | `.50536.1.3.1.1` | **`.50536.1.2.1.1`** |
| L2ARC | `.50536.1.5.x` | **`.50536.1.4.x`** |
| ZIL | `.50536.1.6.x` | **`.50536.1.5.x`** |

## Pré-requisitos / Instalação

1. Habilitar SNMP no TrueNAS: **Services → SNMP → Enable** (v2c, community `public` p/ lab)
2. Importar `Templates/TrueNAS/LT_TrueNAS.yaml` no Zabbix
3. Vincular ao host (SNMP v2c, community `public`)
4. Aguardar ~1h para as LLDs rodarem

## Macros principais

| Macro | Padrão | Descrição |
|-------|--------|-----------|
| `{$ZPOOL.PUSED.MAX.WARN}` | 80 | Alerta de pool em % |
| `{$ZPOOL.PUSED.MAX.CRIT}` | 90 | Crítico de pool em % |
| `{$DATASET.PUSED.MAX.WARN}` | 80 | Alerta de dataset em % |
| `{$ARC.HITRATIO.MIN.WARN}` | 80 | ARC hit ratio baixo |
| `{$SNAPSHOT.AGE.MAX.WARN}` | 604800 | Snapshot > 7 dias (segundos) |

## LLDs (2 regras)
- **ZFS pools discovery** (OID `.1.1.1.1.2`) → health, IOPS, bytes
- **ZFS datasets discovery** (OID `.1.6.1.1.2`, 25.10+) → used/avail/forecast

## Triggers (principais)
- Pool não ONLINE = **HIGH**
- Dataset >80% = WARNING / >90% = AVERAGE
- Dataset cheio em <30 dias = WARNING
- ARC hit ratio <80% = WARNING (memória sob pressão)
- ICMP down / SNMP unavailable = HIGH/WARNING

## Validação
Testado em:
- `truenas01` (192.168.2.217) — TrueNAS SCALE 25.10.6
- Pool `tank` (MIRROR) com dataset `tank/backup`
- Zabbix Server 7.0.30 LTS

## Nota de validação (v0.6.0)
- Scrub: TRUENAS-MIB 25.10 NÃO expõe OID de último scrub (verificado por
  snmpwalk e pelo template oficial). Monitoramento de scrub entra na v0.6.1
  via SNMP traps (.1.3.6.1.4.1.50536.2) com snmptrapd no zabbix1.
- Temperatura de disco: em VMs sem sensor o hddTempTable retorna 0 C; as
  triggers só disparam para temperatura ALTA (sem falso positivo).

## Instalação

### Pré-requisitos

- Zabbix Server 7.0 LTS
- TrueNAS SCALE 25.10+
- SNMP habilitado no TrueNAS
- `net-snmp-utils` e `net-snmp-perl` no servidor Zabbix

### Procedimento

#### 1. Habilitar SNMP no TrueNAS (Web UI)

1. Acesse a interface web do TrueNAS
2. System → Services → SNMP → Enable
3. Configure:
   - SNMP v2c
   - Community: `public` (ou outra de sua preferência)
   - Log level: 3 (warnings)

#### 2. Configurar traps no servidor Zabbix

~~~bash
# Instalar dependências
sudo dnf install -y net-snmp-utils net-snmp-perl

# Criar diretório de scripts
sudo mkdir -p /usr/lib/zabbix

# Baixar receiver oficial do Zabbix
sudo wget -O /usr/lib/zabbix/zabbix_trap_receiver.pl \
  https://raw.githubusercontent.com/zabbix/zabbix/master/misc/snmptrap/zabbix_trap_receiver.pl

# Configurar snmptrapd
sudo tee /etc/snmp/snmptrapd.conf > /dev/null << 'EOCONF'
authCommunity log,execute,net public
perl do "/usr/lib/zabbix/zabbix_trap_receiver.pl";
EOCONF

# Criar diretório de log
sudo mkdir -p /var/log/snmptrap
sudo touch /var/log/snmptrap/snmptrap.log
sudo chown root:zabbix /var/log/snmptrap/snmptrap.log
sudo chmod 644 /var/log/snmptrap/snmptrap.log

# Habilitar e iniciar snmptrapd
sudo systemctl enable --now snmptrapd

# Liberar porta no firewalld
sudo firewall-cmd --add-port=162/udp --permanent
sudo firewall-cmd --reload
~~~

#### 3. Configurar Zabbix Server para ler traps

Edite `/etc/zabbix/zabbix_server.conf`:

~~~bash
sudo tee -a /etc/zabbix/zabbix_server.conf > /dev/null << 'EOCONF'

# SNMP Trapper
StartSNMPTrapper=1
SNMPTrapperFile=/var/log/snmptrap/snmptrap.log
EOCONF

sudo systemctl restart zabbix-server
~~~

#### 4. Importar template e vincular ao host

1. Data collection → Templates → Import → `Templates/TrueNAS/LT_TrueNAS.yaml`
2. Data collection → Hosts → [host do TrueNAS] → Link → `LT TrueNAS` → Update
3. Configure SNMP no host:
   - SNMP version: 2
   - Community: `public`
4. Monitoring → Latest data → filtro `truenas`

#### 5. Testar traps

No servidor Zabbix, envie trap de teste:

~~~bash
snmptrap -v 2c -c public localhost "" 1.3.6.1.4.1.50536.2.1 \
  1.3.6.1.4.1.50536.2.1.1 s "Test trap"
~~~

Verificar em Monitoring → Problems: deve aparecer "TrueNAS: SNMP trap received"

## Troubleshooting

### Traps não chegam ao Zabbix
Verificar firewalld: `sudo firewall-cmd --list-ports` (deve incluir 162/udp)

### SELinux bloqueando traps
Verificar: `sudo getenforce`
Se `Enforcing`, criar módulo:

~~~bash
sudo grep snmptrap /var/log/audit/audit.log | audit2allow -M snmptrap
sudo semodule -i snmptrap.pp
~~~

### Script perl não está escrevendo no log
Verificar: `sudo tail -f /var/log/snmptrap/snmptrap.log` enquanto envia trap
