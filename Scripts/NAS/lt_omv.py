#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenMediaVault Zabbix Collector (lt_omv.py)
LIDORIO TECH - Lidorio-Zabbix-Pack v0.7.0 (lib_lt refactor)
"""

import json
import sys
import requests
import time
import os

# Import lib_lt
sys.path.insert(0, "/etc/zabbix/lib")
try:
    import lib_lt
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
    import lib_lt

LOG = lib_lt.get_logger("omv")

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
        """Load config using lib_lt, with OMV-specific defaults."""
        defaults = {
            'omv_url': 'http://localhost',
            'username': 'admin',
            'password': '',
            'verify_ssl': 'False'
        }
        cfg = lib_lt.load_config(config_file, defaults)
        # Convert verify_ssl string to boolean
        cfg['verify_ssl'] = cfg.get('verify_ssl', 'False').lower() == 'true'
        return cfg
    
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
                LOG.error(f"authentication failed: {data['error']}")
                return False
            
            self.authenticated = True
            LOG.info("authentication successful")
            return True
        except Exception as e:
            LOG.error(f"authentication error: {e}")
            return False
    
    def _rpc_call(self, service, method, params=None):
        if not self.authenticated:
            LOG.error(f"RPC call {service}.{method} skipped: not authenticated")
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
                LOG.error(f"RPC {service}.{method} failed: {data['error']}")
                return None
            
            return data.get('response')
        except Exception as e:
            LOG.error(f"RPC call error: {e}")
            return None
    
    def _load_cache(self):
        if not os.path.exists(CACHE_FILE):
            return None
        
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            if time.time() - cache.get('timestamp', 0) < CACHE_TTL:
                LOG.info("cache hit")
                return cache['data']
        except Exception as e:
            LOG.warning(f"cache read error: {e}")
        
        return None
    
    def _save_cache(self, data):
        try:
            cache = {
                'timestamp': time.time(),
                'data': data
            }
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f)
            LOG.info("cache saved")
        except Exception as e:
            LOG.warning(f"cache write error: {e}")
    
    def _collect_all_data(self):
        LOG.info("starting full data collection")
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
        
        LOG.info(f"collected {len(data['filesystems'])} filesystems, {len(data['disks'])} disks")
        return data
    
    def ping(self):
        result = 1 if self.authenticated else 0
        LOG.info(f"ping: {result}")
        return result
    
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
        
        LOG.info(f"discover filesystems: {len(discovery)}")
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
        
        LOG.info(f"discover disks: {len(discovery)}")
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
        
        LOG.warning(f"filesystem not found: {fsname}")
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
                        except Exception as e:
                            LOG.error(f"temperature parse error for {diskname}: {e}")
                            return 0
                    return 0
                elif metric == 'powermode':
                    return 1 if disk.get('powermode') == 'ACTIVE or IDLE' else 0
        
        LOG.warning(f"disk not found: {diskname}")
        return 0
    
    def _parse_size(self, size_str):
        if not size_str or size_str == '0 B':
            return 0
        
        parts = size_str.split()
        if len(parts) != 2:
            LOG.warning(f"invalid size format: {size_str}")
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
        LOG.error("no command provided")
        lib_lt.emit("Uso: lt_omv.py <comando> [args]", exit_code=1)
    
    collector = OMVCollector()
    command = sys.argv[1]
    
    try:
        if command == 'ping':
            lib_lt.emit(collector.ping())
        
        elif command == 'discover_filesystems':
            lib_lt.emit(collector.discover_filesystems())
        
        elif command == 'discover_disks':
            lib_lt.emit(collector.discover_disks())
        
        elif command == 'fs':
            if len(sys.argv) != 4:
                lib_lt.emit("Uso: lt_omv.py fs <fsname> <metric>", exit_code=1)
            lib_lt.emit(collector.get_fs_metric(sys.argv[2], sys.argv[3]))
        
        elif command == 'disk':
            if len(sys.argv) != 4:
                lib_lt.emit("Uso: lt_omv.py disk <diskname> <metric>", exit_code=1)
            lib_lt.emit(collector.get_disk_metric(sys.argv[2], sys.argv[3]))
        
        else:
            LOG.error(f"unknown command: {command}")
            lib_lt.emit(f"Comando desconhecido: {command}", exit_code=1)
    except Exception as e:
        LOG.error(f"unhandled exception: {e}", exc_info=True)
        lib_lt.emit(-1, exit_code=1)

if __name__ == '__main__':
    main()
