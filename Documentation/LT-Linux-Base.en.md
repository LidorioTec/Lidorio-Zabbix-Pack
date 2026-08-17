# LT Linux Base

Foundation template for Linux systems in the Lidorio-Zabbix-Pack.

## Version

v0.1.0 - validated on 2026-08-16 on Zabbix 7.0.29 LTS.

## Compatibility

- Zabbix 7.0 LTS (official validation target)
- Zabbix Agent 2

## Prerequisites

- Zabbix Agent 2 installed and reachable.
- Do NOT link together with "Linux by Zabbix agent" (duplicate keys).

## Items (18)

- CPU: system.cpu.util, system.cpu.load[all,avg1]
- Memory: vm.memory.size[total|available|pavailable|pused]
- Swap: system.swap.size[total|free|pfree]
- System: system.uptime, system.hostname, system.uname,
  system.sw.os, system.sw.arch
- Processes: proc.num, kernel.maxfiles, kernel.maxproc, kernel.openfiles

## Discovery rules (2)

### Filesystem discovery
- Key: vfs.fs.discovery - interval: 1h
- Filter: {#FSTYPE} matches ^(xfs|ext2|ext3|ext4|btrfs|zfs|reiserfs|jfs)$
- Prototypes: vfs.fs.size[{#FSNAME},free|total|used|pused]
- Trigger prototype: filesystem full (HIGH) using {$FS.PUSED.HIGH}

### Network interface discovery
- Key: net.if.discovery - interval: 1h
- Filter: {#IFNAME} matches ^(eth|en|bond|br|vlan)
- Prototypes: net.if.in[{#IFNAME}], net.if.out[{#IFNAME}]
  (CHANGE_PER_SECOND), net.if.in[{#IFNAME},errors]
- Trigger prototype: inbound errors (AVERAGE) using {$IF.ERRORS.WARN}

## Macros (9)

| Macro | Default | Description |
|-------|---------|-------------|
| {$CPU.UTIL.HIGH} | 90 | CPU utilization warning (%) |
| {$CPU.UTIL.DISASTER} | 95 | CPU utilization critical (%) |
| {$MEM.PUSED.HIGH} | 90 | Memory usage warning (%) |
| {$MEM.PUSED.DISASTER} | 95 | Memory usage critical (%) |
| {$SWAP.PUSED.HIGH} | 50 | Swap usage warning (%) |
| {$FS.PUSED.HIGH} | 90 | Filesystem usage warning (%) |
| {$FS.PUSED.DISASTER} | 95 | Filesystem usage critical (%) |
| {$IF.ERRORS.WARN} | 10 | Interface error threshold |
| {$LOAD.AVG.HIGH} | 5 | Load average (1m) warning |

## Triggers (5)

- CPU utilization is too high (WARNING)
- CPU load average is too high (WARNING)
- Memory utilization is too high (WARNING)
- Swap utilization is too high (WARNING)
- Host has been restarted (INFO)

## Tags

- component:system, component:cpu, component:memory,
  component:storage, component:network, component:agent
- service:linux
- target:LT Linux Base

## Troubleshooting

- "Not supported" items such as VMware/IPMI/Java/connectors belong to the
  stock "Zabbix server health" template, not to this template.
- Valid LLD macros on Agent 2 (7.0): {#FSNAME}, {#FSTYPE}, {#FSOPTIONS},
  {#IFNAME}. Do not use {#FSPROBE} or {#FSLABEL}.
- When testing a "greater than" trigger, set the temporary macro below the
  current value, otherwise the condition never becomes true.

## Validation (zabbix_get)

    zabbix_get -s 127.0.0.1 -k system.cpu.util
    zabbix_get -s 127.0.0.1 -k vm.memory.size[pused]
    zabbix_get -s 127.0.0.1 -k vfs.fs.discovery
    zabbix_get -s 127.0.0.1 -k net.if.discovery

## Version history

- v0.1.0 (2026-08-16): first release, validated on Zabbix 7.0 LTS.
