#!/bin/bash
# ============================================================================
# LIDORIO TECH - Multi-distro compatibility library
# Version: 1.0.0 (v0.7.0-base)
# Purpose: Provide portable functions across Debian/Ubuntu/RHEL/Rocky/Alma
# ============================================================================

# ----------------------------------------------------------------------------
# Detect OS family
# Returns: debian | redhat | arch | unknown
# ----------------------------------------------------------------------------
detect_family() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            debian|ubuntu|linuxmint|pop) echo "debian" ;;
            rhel|rocky|alma|fedora|centos|ol) echo "redhat" ;;
            arch|manjaro) echo "arch" ;;
            *) echo "unknown" ;;
        esac
    else
        echo "unknown"
    fi
}

# ----------------------------------------------------------------------------
# Detect Zabbix agent service name
# Returns: zabbix-agent2 | zabbix-agent | (empty)
# ----------------------------------------------------------------------------
detect_agent_service() {
    for svc in zabbix-agent2 zabbix-agent; do
        if systemctl list-unit-files 2>/dev/null | grep -q "^${svc}\.service"; then
            echo "$svc"
            return 0
        fi
    done
    echo ""
    return 1
}

# ----------------------------------------------------------------------------
# Install packages (portable)
# Usage: pkg_install <pkg1> [pkg2] ...
# ----------------------------------------------------------------------------
pkg_install() {
    local family
    family=$(detect_family)
    case "$family" in
        debian) apt-get install -y "$@" ;;
        redhat) dnf install -y "$@" ;;
        arch)   pacman -S --noconfirm "$@" ;;
        *) echo "ERROR: unsupported family ($family)" >&2; return 1 ;;
    esac
}

# ----------------------------------------------------------------------------
# Restart a service (portable)
# Usage: service_restart <service>
# ----------------------------------------------------------------------------
service_restart() {
    systemctl restart "$1" 2>/dev/null || service "$1" restart 2>/dev/null
}

# ----------------------------------------------------------------------------
# Enable + start a service (portable)
# Usage: service_enable <service>
# ----------------------------------------------------------------------------
service_enable() {
    systemctl enable --now "$1" 2>/dev/null
}

# ----------------------------------------------------------------------------
# Check if user exists
# Usage: user_exists <user>
# ----------------------------------------------------------------------------
user_exists() {
    id "$1" >/dev/null 2>&1
}

# ----------------------------------------------------------------------------
# Check if group exists
# Usage: group_exists <group>
# ----------------------------------------------------------------------------
group_exists() {
    getent group "$1" >/dev/null 2>&1
}

# ----------------------------------------------------------------------------
# Install a script with correct ownership
# Usage: install_script <src> <dst> [mode]
# ----------------------------------------------------------------------------
install_script() {
    local src="$1" dst="$2" mode="${3:-755}"
    local owner="root" group="root"
    group_exists zabbix && group="zabbix"
    install -m "$mode" -o "$owner" -g "$group" "$src" "$dst"
}

# ----------------------------------------------------------------------------
# Open a port in the firewall (portable: firewalld/ufw/iptables)
# Usage: open_port <port>/<proto>  e.g. open_port 162/udp
# ----------------------------------------------------------------------------
open_port() {
    local port_proto="$1"
    if command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --add-port="$port_proto" --permanent
        firewall-cmd --reload
    elif command -v ufw >/dev/null 2>&1; then
        ufw allow "$port_proto"
    else
        echo "WARN: no supported firewall tool found; open $port_proto manually" >&2
    fi
}

# ----------------------------------------------------------------------------
# Check SELinux status and optionally set permissive
# Usage: selinux_status
# ----------------------------------------------------------------------------
selinux_status() {
    if command -v getenforce >/dev/null 2>&1; then
        getenforce
    else
        echo "Disabled"
    fi
}
