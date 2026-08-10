# Lidorio-Zabbix-Pack

Open-source Zabbix templates and monitoring components developed by **LIDORIO TECH**.

## About

The Lidorio-Zabbix-Pack is an open-source project created by LIDORIO TECH to provide standardized, maintainable and scalable Zabbix templates and monitoring components.

The project is designed as part of the LIDORIO TECH ecosystem. The templates and monitoring components are publicly available, while other solutions and services of the LIDORIO TECH ecosystem may remain private.

## Project Structure

```text
Lidorio-Zabbix-Pack/
├── Templates/
├── Dashboards/
├── Maps/
├── MediaTypes/
├── Actions/
├── Scripts/
├── Documentation/
└── README.md
```

## Development Roadmap

The development sequence defined for the project is:

1. LT Linux Base
2. LT Bareos
3. LT NAS / Storage

   * OpenMediaVault
   * TrueNAS
4. Dashboard Executivo de Backup
5. Dashboard Técnico Bareos
6. LT OPNsense
7. LT MikroTik
8. LT PostgreSQL
9. LT MariaDB
10. LT Samba AD
11. LT Docker

## LT Linux Base

The LT Linux Base will be the foundation of the other Linux-based templates.

The initial scope includes:

* CPU
* Memory
* Swap
* Filesystems
* Disks
* Network
* Processes
* Uptime
* Load
* Services
* Zabbix Agent availability
* Low-Level Discovery (LLD)

Specific templates will inherit the LT Linux Base whenever applicable, avoiding unnecessary duplication.

## LT Bareos

LT Bareos will be one of the main specialized templates of the project.

The planned monitoring scope includes:

### Bareos Services

* Director
* Storage Daemon
* File Daemon
* Service status
* Availability

### Jobs

* Execution
* Success / failure
* Duration
* Size
* Throughput
* Stuck jobs
* Delayed jobs
* Last backup

### Backup Policy

* Last Full
* Last Differential
* Last Incremental
* Age of last backup
* Clients without recent backups

### Storage

* Used space
* Free space
* Growth
* Volumes
* Pools
* Scratch
* Available capacity

### Catalog

* PostgreSQL
* Catalog availability
* Connection problems
* Relevant performance indicators

### Security and Continuity

* Backup failures
* Absence of recent backups
* Abnormal behavior
* Indicators that may help identify situations related to ransomware

Low-Level Discovery (LLD) will be used where appropriate to provide scalability.

## Dashboards

The project includes two planned Bareos dashboards:

### Executive Backup Dashboard

Designed for customers and management, providing a high-level view of backup protection and status.

### Technical Bareos Dashboard

Designed for the LIDORIO TECH technical team, providing detailed information about jobs, errors, duration, throughput, volumes, pools, storage, clients, daemons, PostgreSQL, history and trends.

## LIDORIO TECH Standardization

The project follows a standardized LIDORIO TECH approach for:

* Tags
* Severities
* Naming conventions
* Macros
* Discovery rules
* Items
* Triggers
* Templates
* Dashboards
* Maps
* Media Types
* Actions
* Scripts
* Documentation

## Zabbix Version

The development and validation baseline for the current project version is:

**Zabbix 7.0 LTS**

## Project Status

**Status: Initial development**

The project is currently being developed and validated in a laboratory environment.

## License

License information will be defined before the first public release.
