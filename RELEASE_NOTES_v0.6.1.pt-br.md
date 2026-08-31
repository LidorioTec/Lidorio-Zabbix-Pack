# Lidorio-Zabbix-Pack v0.6.1 — Versão Estável

**Data de lançamento:** 30 de agosto de 2026
**Status:** Estável para produção

---

## O que foi entregue nesta versão

### LT TrueNAS v0.6.1 — Monitoramento de Scrub via SNMP Traps

**Problema resolvido:** A TRUENAS-MIB 25.10 não expõe o timestamp do
último scrub via polling SNMP (verificado por snmpwalk + análise do
template oficial do Zabbix). Sem essa métrica, pools ZFS podem ficar
meses sem scrub, acumulando corrupção silenciosa (bit rot) sem alerta.

**Solução implementada:** pipeline completo de SNMP traps:

~~~
TrueNAS (truenas01)
  | envia trap quando scrub completa/falha (OID .1.3.6.1.4.1.50536.2)
  v
firewalld (zabbix1, porta 162/UDP)
  v
snmptrapd (zabbix1) + zabbix_trap_receiver.pl
  v
/var/log/snmptrap/snmptrap.log
  v
Zabbix Server (SNMPTrapperFile + StartSNMPTrapper=1)
  v
Item SNMP_TRAP: snmptrap[.*50536\.2.*]
  v
Triggers: HIGH (scrub failed) + AVERAGE (scrub found errors)
~~~

**Itens adicionados:**
- `TrueNAS: SNMP traps (alert/scrub events)` — captura traps da MIB TrueNAS

**Triggers adicionadas:**
- HIGH `TrueNAS: Scrub failed (trap)` — trap contém "failed"
- AVERAGE `TrueNAS: Scrub found errors (trap)` — trap contém "errors"
- Ambas com `manual_close: YES` (traps são eventos stateless)

---

## Problemas resolvidos nesta versão

| # | Problema | Causa raiz | Solução |
|---|----------|------------|---------|
| 1 | Traps não chegavam | firewalld: 162/udp só no permanent | `--add-port` + `--reload` |
| 2 | Perl escrevia no caminho errado | `/tmp/zabbix_traps.tmp` hardcoded | sed p/ `/var/log/snmptrap/snmptrap.log` |
| 3 | SELinux bloqueava | snmpd_t write + zabbix_t read denied | lab: permissive; prod: módulo audit2allow |
| 4 | Scrub via polling "No Such Object" | OID .1.1.1.1.12 não existe na 25.10 | removido; scrub via traps |
| 5 | "unexpected tag triggers" no import | triggers no nível do template | movidas para dentro do item |

---

## Validação técnica

**Ambiente:** Zabbix 7.0.30 LTS (Rocky 10.2) + TrueNAS SCALE 25.10.6 + snmptrapd 5.9.4

**Método:** snmpwalk da MIB completa; análise do template oficial 7.4;
trap manual via `snmptrap`; validação no log; import; disparo das
triggers; manual close; reenvio.

**Resultado:** pipeline funcional em < 5s do envio do trap.

---

## Compatibilidade

| Componente | Versão testada | Observações |
|------------|----------------|-------------|
| Zabbix Server | 7.0.30 LTS | `StartSNMPTrapper=1` no zabbix_server.conf |
| TrueNAS SCALE | 25.10.6 | SNMP v2c (lab) ou v3 (prod) |
| snmptrapd | 5.9.4 | requer `net-snmp-perl` |
| firewalld | 1.3.x | 162/udp na runtime |
| SELinux | Rocky 10.2 | permissive (lab) ou módulo (prod) |

---

## Como usar

1. Importe `Templates/TrueNAS/LT_TrueNAS.yaml` no Zabbix
2. Host TrueNAS com SNMP v2c
3. No servidor Zabbix: `net-snmp-perl` + snmptrapd.conf com
   `perl do "/usr/lib/zabbix/zabbix_trap_receiver.pl"` +
   `StartSNMPTrapper=1` + `firewall-cmd --add-port=162/udp --permanent && --reload`
4. Envie trap manual ou aguarde o próximo scrub
5. Valide em Monitoring -> Problems

---

## Estado do projeto após v0.6.1

~~~
v0.1.0  LT Linux Base
v0.2.0  LT Bareos
v0.3.0  LT NAS Storage (OMV)
v0.4.0  LT RustFS
v0.5.x  LT TrueNAS (MIB 25.10 + forecast + L2ARC/ZIL/temp)
v0.6.0  RPO/staleness/ZFS-depth
v0.6.1  Scrub via SNMP traps  <- ESTA VERSAO
~~~

Pipeline completo de backup monitorado:

~~~
Bareos (backup01) -> NAS (storage01/OMV) -> Restic -> RustFS (rustfs01)
   LT Bareos         LT NAS Storage                   LT RustFS
                                               +
                                         TrueNAS (truenas01)
                                          LT TrueNAS
~~~

---

## Próximos passos (v0.7.0+)

- v0.7.0 — Procedimentos de instalação multi-distro + lib de compatibilidade
- v0.8.0 — Dashboard Executivo de Backup
- v0.9.0 — Novos templates (OPNsense, MikroTik, PostgreSQL, etc.)

**Autor:** Edson Lidorio | **Licença:** GPL-3.0
**Repo:** https://github.com/LidorioTec/Lidorio-Zabbix-Pack
