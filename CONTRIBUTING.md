# Contributing to Lidorio-Zabbix-Pack

Thank you for considering a contribution! This document explains how to
report bugs, suggest features and send pull requests.

## Reporting bugs

1. Open an issue using the **Bug report** template.
2. Include versions: Zabbix server/agent, template, platform.
3. Test keys with `zabbix_get` when possible and paste the output.
4. NEVER include passwords, API keys, tokens or private data.

## Suggesting features

Open an issue using the **Feature request** template.

## Security vulnerabilities

Do NOT open public issues for security problems.
Email lidoriotech@gmail.com instead (see SECURITY.md).

## Pull requests

1. Fork the repository and create a branch.
2. Follow the project standards:
   - All Zabbix objects (items, triggers, macros, tags) in English
   - Thresholds via macros, never hardcoded
   - Use LLD (Low-Level Discovery) wherever it makes sense
   - No false positives when a platform lacks a sensor/metric
   - Validate on Zabbix 7.0 LTS before submitting
   - Never commit credentials (use .example files with placeholders)
3. Use Conventional Commits in English, e.g. `feat: add X`, `fix: Y`.
4. Open the pull request describing what was tested and where.

## Support the project

See the "Support the Project" section in the README (PIX / PayPal).
