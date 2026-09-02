# Lidorio-Zabbix-Pack
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

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
| LT Bareos | Bareos backup suite (Director, SD, FD, jobs, storage, catalog) | v0.2.0 |
| LT NAS / Storage | NAS and storage systems | v0.3.0 |
| LT OPNsense | OPNsense firewalls | planned |
| LT MikroTik | MikroTik routers | planned |
| LT PostgreSQL | PostgreSQL databases | planned |
| LT MariaDB | MariaDB databases | planned |
| LT Samba AD | Samba Active Directory | planned |
| LT Docker | Docker containers | planned |
| LT RustFS | RustFS S3 object storage (buckets, nodes, cluster health, capacity) | v0.4.0 |

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

Each template ships bilingual documentation:

- **LT Linux Base**
  - English: Documentation/LT-Linux-Base.en.md
  - Portugues: Documentation/LT-Linux-Base.pt-br.md
- **LT Bareos**
  - English: Documentation/LT-Bareos.en.md
  - Portugues: Documentation/LT-Bareos.pt-br.md
- **LT NAS / Storage**
  - English: Documentation/LT-NAS-Storage.en.md
  - Portugues: Documentation/LT-NAS-Storage.pt-br.md

## Naming and Standards

- Template prefix: LT (LIDORIO TECH)
- Template group: Lidorio Tech
- All Zabbix objects (items, triggers, macros, tags) in English
- Thresholds via macros, never hardcoded
- Conventional Commits in English

## Contributing

Forks, issues and pull requests are welcome.

## 💖 Support the Project

If Lidorio-Zabbix-Pack helps your operation and you want to support its
continued development, contributions are welcome:

### 🇧🇷 PIX (Brazil)

Key: `lidoriotech@gmail.com`

<p align="center">
  <img src="assets/pix-qrcode.png" alt="PIX QR Code" width="220"/>
</p>

### 🌍 PayPal (International)

[Donate with PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=lidoriotech@gmail.com)

Thank you for supporting open source! 🙏

##  License

This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE](LICENSE) file for details.

## About

Lidorio-Zabbix-Pack is the public layer of the LIDORIO TECH monitoring
ecosystem. Commercial and private solutions remain separate.

## Convenção de documentação (Documentation Convention)

Todos os arquivos de documentação seguem o padrão bilíngue:

All documentation files follow the bilingual standard:

| Tipo / Type | Convenção / Convention |
|-------------|------------------------|
| Docs por template | `LT-X.pt-br.md` + `LT-X.en.md` |
| Release Notes | `RELEASE_NOTES_vX.Y.Z.pt-br.md` + `RELEASE_NOTES_vX.Y.Z.en.md` |
| Procedimentos | seções PT-BR e EN dentro de cada doc |
| Cercas de código | usar `~~~` em vez de ``` para não quebrar heredocs |
