#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenMediaVault Zabbix Collector (lt_omv.py)
LIDORIO TECH - Lidorio-Zabbix-Pack v0.3.0
"""

import json
import sys
import requests
import time
import os

CONFIG_FILE = "/etc/zabbix/scripts/lt_omv.conf"
CACHE_FILE = "/tmp/lt_omv_cache.json"
CACHE_TTL = 120

class OMVCollector:
    def __init__(self, config_file=CONFIG_FILE):
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.authenticated = False
        self._authenticate()
    
    def _load_config(self, config_file):
        config = {
            'omv_url': 'http://localhost',
            'username': 'admin',
            'password': '',
            'verify_ssl': False
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        return config
    
    def _authenticate(self):
        try:
            url = f"{self.config['omv_url']}/rpc.php"
            payload = {
                "service": "Session",
                "method": "login",
                "params": {
                    "username": self.config['username'],
                    "password": self.config['password']
                }
            }
            
            response = self.session.post(url, json=payload, verify=self.config['verify_ssl'], timeout=10)
            data = response.json()
            
            if data.get('error'):
                print(f"Erro de autenticação: {data['error']}", file=sys.stderr)
                return False
            
            self.authenticated = True
            return True
        except Exception as e:
            print(f"Erro ao autenticar: {e}", file=sys.stderr)
            return False
    
    def _rpc_call(self, service, method, params=None):
        if not self.authenticated:
            return None
        
        if params is None:
            params = {}
        
        try:
            url = f"{self.config['omv_url']}/rpc.php"
            payload = {
                "service": service,
                "method": method,
                "params": params
            }
            
            response = self.session.post(url, json=payload, verify=self.config['verify_ssl'], timeout=10)
            data = response.json()
            
            if data.get('error'):
                print(f"Erro RPC {service}.{method}: {data['error']}", file=sys.stderr)
                return None
            
            return data.get('response')
        except Exception as e:
            print(f"Erro na chamada RPC: {e}", file=sys.stderr)
            return None
    
    def _load_cache(self):
        if not os.path.exists(CACHE_FILE):
            return None
        
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            if time.time() - cache.get('timestamp', 0) < CACHE_TTL:
                return cache['data']
        except:
            pass
        
        return None
    
    def _save_cache(self, data):
        try:
            cache = {
                'timestamp': time.time(),
                'data': data
            }
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f)
        except:
            pass
    
    def _collect_all_data(self):
        data = {
            'filesystems': [],
            'disks': []
        }
        
        fs_data = self._rpc_call('FileSystemMgmt', 'enumerateFilesystems')
        if fs_data:
                data['filesystems'] = [
                fs for fs in fs_data
                if fs.get('mounted', False)
                and fs.get('type') != 'swap'
                and not fs.get('_readonly', True)
            ]
        
        disk_data = self._rpc_call('DiskMgmt', 'enumerateDevices')
        if disk_data:
            data['disks'] = disk_data
        
        return data
    
    def ping(self):
        return 1 if self.authenticated else 0
    
    def discover_filesystems(self):
        cache = self._load_cache()
        if not cache:
            cache = self._collect_all_data()
            self._save_cache(cache)
        
        discovery = []
        for fs in cache.get('filesystems', []):
            discovery.append({
                '{#FSNAME}': fs.get('devicename'),
                '{#FSMOUNT}': fs.get('mountpoint'),
                '{#FSTYPE}': fs.get('type'),
                '{#FSUUID}': fs.get('uuid')
            })
        
        return json.dumps({'data': discovery})
    
    def discover_disks(self):
        cache = self._load_cache()
        if not cache:
            cache = self._collect_all_data()
            self._save_cache(cache)
        
        discovery = []
        for disk in cache.get('disks', []):
            discovery.append({
                '{#DISKNAME}': disk.get('devicename'),
                '{#DISKMODEL}': disk.get('model', ''),
                '{#DISKSERIAL}': disk.get('serialnumber', ''),
                '{#DISKSIZE}': disk.get('size', '0')
            })
        
        return json.dumps({'data': discovery})
    
    def get_fs_metric(self, fsname, metric):
        cache = self._load_cache()
        if not cache:
            cache = self._collect_all_data()
            self._save_cache(cache)
        
        for fs in cache.get('filesystems', []):
            if fs.get('devicename') == fsname:
                if metric == 'total':
                    return fs.get('size', '0')
                elif metric == 'used':
                    used_str = fs.get('used', '0 B')
                    return self._parse_size(used_str)
                elif metric == 'available':
                    return fs.get('available', '0')
                elif metric == 'percentage':
                    return fs.get('percentage', 0)
        
        return 0
    
    def get_disk_metric(self, diskname, metric):
        cache = self._load_cache()
        if not cache:
            cache = self._collect_all_data()
            self._save_cache(cache)
        
        for disk in cache.get('disks', []):
            if disk.get('devicename') == diskname:
                if metric == 'size':
                    return disk.get('size', '0')
                elif metric == 'temperature':
                    temp = disk.get('temperature', '')
                    if temp:
                        try:
                            return int(''.join(filter(str.isdigit, temp.split()[0] if temp else '0')))
                        except:
                            return 0
                    return 0
                elif metric == 'powermode':
                    return 1 if disk.get('powermode') == 'ACTIVE or IDLE' else 0
        
        return 0
    
    def _parse_size(self, size_str):
        if not size_str or size_str == '0 B':
            return 0
        
        parts = size_str.split()
        if len(parts) != 2:
            return 0
        
        value = float(parts[0])
        unit = parts[1].upper()
        
        multipliers = {
            'B': 1,
            'KIB': 1024,
            'MIB': 1024**2,
            'GIB': 1024**3,
            'TIB': 1024**4
        }
        
        return int(value * multipliers.get(unit, 1))

def main():
    if len(sys.argv) < 2:
        print("Uso: lt_omv.py <comando> [args]", file=sys.stderr)
        sys.exit(1)
    
    collector = OMVCollector()
    command = sys.argv[1]
    
    if command == 'ping':
        print(collector.ping())
    
    elif command == 'discover_filesystems':
        print(collector.discover_filesystems())
    
    elif command == 'discover_disks':
        print(collector.discover_disks())
    
    elif command == 'fs':
        if len(sys.argv) != 4:
            print("Uso: lt_omv.py fs <fsname> <metric>", file=sys.stderr)
            sys.exit(1)
        print(collector.get_fs_metric(sys.argv[2], sys.argv[3]))
    
    elif command == 'disk':
        if len(sys.argv) != 4:
            print("Uso: lt_omv.py disk <diskname> <metric>", file=sys.stderr)
            sys.exit(1)
        print(collector.get_disk_metric(sys.argv[2], sys.argv[3]))
    
    else:
        print(f"Comando desconhecido: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
