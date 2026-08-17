# Lidorio-Zabbix-Pack

A standardized Zabbix monitoring framework by LIDORIO TECH.

## Overview

Lidorio-Zabbix-Pack is the public, open-source monitoring framework of
LIDORIO TECH. It provides production-ready Zabbix templates, dashboards,
maps, media types, actions and scripts built on four principles:

- **Reuse** - build once, use across many environments.
- **Scalability** - Low-Level Discovery (LLD) wherever it makes sense.
- **Standardization** - every template looks like part of the same product.
- **Validation** - nothing is released without testing on Zabbix 7.0 LTS.

## Architecture

Templates follow an inheritance model. LT Linux Base is the foundation;
specialized templates inherit from it and add only service-specific
monitoring:

    LT Linux Base
        |-- LT Bareos
        |-- LT NAS / Storage
        |-- LT OPNsense
        |-- LT MikroTik
        |-- LT PostgreSQL
        |-- LT MariaDB
        |-- LT Samba AD
        `-- LT Docker

## Templates

| Template | Description | Status |
|----------|-------------|--------|
| LT Linux Base | Foundation template for Linux systems | v0.1.0 |
| LT Bareos | Bareos backup suite (Director, SD, FD, jobs, storage, catalog) | planned |
| LT NAS / Storage | NAS and storage systems | planned |
| LT OPNsense | OPNsense firewalls | planned |
| LT MikroTik | MikroTik routers | planned |
| LT PostgreSQL | PostgreSQL databases | planned |
| LT MariaDB | MariaDB databases | planned |
| LT Samba AD | Samba Active Directory | planned |
| LT Docker | Docker containers | planned |

## Requirements

- Zabbix Server 7.0 LTS (validated on 7.0.29)
- Zabbix Agent 2 on monitored hosts

## Quick Start

1. Import the template:
   - Zabbix UI: Data collection -> Templates -> Import
   - Select Templates/Linux/LT_Linux_Base.yaml
2. Link LT Linux Base to your host.
3. Important: do not combine with the stock "Linux by Zabbix agent"
   template (key conflicts).

## Documentation

- English: Documentation/LT-Linux-Base.en.md
- Portugues: Documentation/LT-Linux-Base.pt-br.md

## Naming and Standards

- Template prefix: LT (LIDORIO TECH)
- Template group: Lidorio Tech
- All Zabbix objects (items, triggers, macros, tags) in English
- Thresholds via macros, never hardcoded
- Conventional Commits in English

## Contributing

Forks, issues and pull requests are welcome.

## About

Lidorio-Zabbix-Pack is the public layer of the LIDORIO TECH monitoring
ecosystem. Commercial and private solutions remain separate.
