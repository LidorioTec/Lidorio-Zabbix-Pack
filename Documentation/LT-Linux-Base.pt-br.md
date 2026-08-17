# LT Linux Base

Template fundacional Linux do Lidorio-Zabbix-Pack. Centraliza indicadores
comuns (CPU, memoria, swap, filesystem, rede, processos) para servir de
base aos templates especializados (LT Bareos, LT PostgreSQL, etc.).

## Versao

v0.1.0 - validado em 16/08/2026 no Zabbix 7.0.29 LTS (zabbix1).

## Compatibilidade

- Zabbix 7.0 LTS (alvo oficial de validacao)
- Zabbix Agent 2

## Pre-requisitos

- Zabbix Agent 2 instalado e respondendo.
- NAO vincular junto com "Linux by Zabbix agent" (conflito de keys).

## Itens (18)

- CPU: system.cpu.util, system.cpu.load[all,avg1]
- Memoria: vm.memory.size[total|available|pavailable|pused]
- Swap: system.swap.size[total|free|pfree]
- Sistema: system.uptime, system.hostname, system.uname,
  system.sw.os, system.sw.arch
- Processos: proc.num, kernel.maxfiles, kernel.maxproc, kernel.openfiles

## Discovery Rules (2)

### Filesystem discovery
- Key: vfs.fs.discovery - intervalo: 1h
- Filtro: {#FSTYPE} =~ ^(xfs|ext2|ext3|ext4|btrfs|zfs|reiserfs|jfs)$
- Prototypes: vfs.fs.size[{#FSNAME},free|total|used|pused]
- Trigger prototype: filesystem cheio (HIGH) via {$FS.PUSED.HIGH}

### Network interface discovery
- Key: net.if.discovery - intervalo: 1h
- Filtro: {#IFNAME} =~ ^(eth|en|bond|br|vlan)
- Prototypes: net.if.in[{#IFNAME}], net.if.out[{#IFNAME}]
  (CHANGE_PER_SECOND), net.if.in[{#IFNAME},errors]
- Trigger prototype: erros de entrada (AVERAGE) via {$IF.ERRORS.WARN}

## Macros (9)

| Macro | Padrao | Descricao |
|-------|--------|-----------|
| {$CPU.UTIL.HIGH} | 90 | Alerta de utilizacao de CPU (%) |
| {$CPU.UTIL.DISASTER} | 95 | Critico de utilizacao de CPU (%) |
| {$MEM.PUSED.HIGH} | 90 | Alerta de uso de memoria (%) |
| {$MEM.PUSED.DISASTER} | 95 | Critico de uso de memoria (%) |
| {$SWAP.PUSED.HIGH} | 50 | Alerta de uso de swap (%) |
| {$FS.PUSED.HIGH} | 90 | Alerta de uso de filesystem (%) |
| {$FS.PUSED.DISASTER} | 95 | Critico de uso de filesystem (%) |
| {$IF.ERRORS.WARN} | 10 | Limiar de erros de interface |
| {$LOAD.AVG.HIGH} | 5 | Alerta de load average (1m) |

## Triggers (5)

- CPU utilization is too high (WARNING)
- CPU load average is too high (WARNING)
- Memory utilization is too high (WARNING)
- Swap utilization is too high (WARNING)
- Host has been restarted (INFO)

(Nomes das triggers em ingles, conforme padrao do projeto.)

## Tags

- component:system, component:cpu, component:memory,
  component:storage, component:network, component:agent
- service:linux
- target:LT Linux Base

## Troubleshooting

- Itens "not supported" de VMware/IPMI/Java/connectors pertencem ao
  template oficial "Zabbix server health", nao a este template.
- Macros LLD validas no Agent 2 (7.0): {#FSNAME}, {#FSTYPE},
  {#FSOPTIONS}, {#IFNAME}. Nao usar {#FSPROBE} ou {#FSLABEL}.
- Ao testar trigger "maior que", use limiar temporario ABAIXO do valor
  atual do item, senao a condicao nunca sera verdadeira.

## Validacao (zabbix_get)

    zabbix_get -s 127.0.0.1 -k system.cpu.util
    zabbix_get -s 127.0.0.1 -k vm.memory.size[pused]
    zabbix_get -s 127.0.0.1 -k vfs.fs.discovery
    zabbix_get -s 127.0.0.1 -k net.if.discovery

## Historico de versoes

- v0.1.0 (16/08/2026): primeira versao validada no Zabbix 7.0 LTS.
