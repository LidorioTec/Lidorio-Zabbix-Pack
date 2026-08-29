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
