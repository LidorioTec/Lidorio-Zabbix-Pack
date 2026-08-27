#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LT RustFS Collector - Lidorio-Zabbix-Pack v0.4.0
Reads health endpoints (no auth) and uses 'rc' CLI for bucket metrics.
"""

import json
import os
import sys
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime

CACHE_FILE = "/tmp/lt_rustfs.cache.json"
CACHE_TTL = 120
ALIAS_NAME = "rustfs_zabbix"

def load_config():
    config = {
        "endpoint": "http://127.0.0.1:9000",
        "access_key": "",
        "secret_key": "",
        "data_path": "/data/rustfs/mnmd"
    }
    conf_file = "/etc/zabbix/scripts/lt_rustfs.conf"
    if os.path.exists(conf_file):
        with open(conf_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

def ensure_alias(config):
    cmd = f'rc alias set {ALIAS_NAME} {config["endpoint"]} "{config["access_key"]}" "{config["secret_key"]}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return result.returncode == 0

def get_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        if time.time() - cache.get('timestamp', 0) < CACHE_TTL:
            return cache
    except:
        pass
    return None

def save_cache(data):
    try:
        cache = {'timestamp': time.time(), 'data': data}
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except:
        pass

def fetch_health(endpoint):
    try:
        url = f"{endpoint}/health"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def fetch_cluster_health(endpoint):
    try:
        url = f"{endpoint}/minio/health/cluster"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

def run_rc_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else None
    except:
        return None

def collect_buckets(config):
    if not ensure_alias(config):
        return []
    
    cmd = f"rc ls {ALIAS_NAME}/ --json"
    output = run_rc_command(cmd)
    
    if not output:
        return []
    
    try:
        data = json.loads(output)
        buckets = []
        for item in data.get('items', []):
            if item.get('is_dir'):
                buckets.append({
                    'key': item['key'].rstrip('/'),
                    'last_modified': item.get('last_modified', '')
                })
        return buckets
    except:
        return []

def collect_bucket_size(config, bucket_name):
    # Use rc ls --recursive --summarize --json
    cmd = f"rc ls {ALIAS_NAME}/{bucket_name}/ --recursive --summarize --json"
    output = run_rc_command(cmd)
    
    if not output:
        return {'objects': 0, 'bytes': 0}
    
    try:
        data = json.loads(output)
        summary = data.get('summary', {})
        return {
            'objects': summary.get('total_objects', 0),
            'bytes': summary.get('total_size_bytes', 0)
        }
    except:
        return {'objects': 0, 'bytes': 0}

def collect_disk_usage(data_path):
    result = {'used_bytes': 0, 'total_bytes': 0, 'used_pct': 0}
    
    output = subprocess.run(f"du -sb {data_path}", shell=True, capture_output=True, text=True)
    if output.returncode == 0:
        parts = output.stdout.split()
        if len(parts) >= 1:
            result['used_bytes'] = int(parts[0])
    
    output = subprocess.run(f"df -B1 {data_path}", shell=True, capture_output=True, text=True)
    if output.returncode == 0:
        lines = output.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 2:
                result['total_bytes'] = int(parts[1])
                if result['total_bytes'] > 0:
                    result['used_pct'] = round((result['used_bytes'] / result['total_bytes']) * 100, 2)
    
    return result

def collect_all(config):
    data = {
        'health': None,
        'cluster': None,
        'buckets': [],
        'disk': None
    }
    
    data['health'] = fetch_health(config['endpoint'])
    data['cluster'] = fetch_cluster_health(config['endpoint'])
    
    buckets = collect_buckets(config)
    for bucket in buckets:
        bucket_name = bucket['key']
        size_info = collect_bucket_size(config, bucket_name)
        data['buckets'].append({
            'name': bucket_name,
            'last_modified': bucket.get('last_modified'),
            'objects': size_info['objects'],
            'bytes': size_info['bytes']
        })
    
    data['disk'] = collect_disk_usage(config['data_path'])
    
    return data

def get_data(config):
    cache = get_cache()
    if cache:
        return cache['data']
    
    data = collect_all(config)
    save_cache(data)
    return data

def cmd_ping(config):
    health = fetch_health(config['endpoint'])
    return 1 if health and health.get('status') == 'ok' else 0

def cmd_health(config, key):
    data = get_data(config)
    health = data.get('health', {})
    if not health:
        return -1
    
    if key == 'status':
        return 1 if health.get('status') == 'ok' else 0
    elif key == 'ready':
        return 1 if health.get('ready') else 0
    elif key == 'version':
        return health.get('version', 'unknown')
    
    return -1

def cmd_cluster(config, component):
    data = get_data(config)
    cluster = data.get('cluster', {})
    if not cluster:
        return -1
    
    details = cluster.get('details', {})
    comp_data = details.get(component, {})
    
    if component == 'status':
        return 1 if cluster.get('status') == 'ok' else 0
    elif component == 'ready':
        return 1 if cluster.get('ready') else 0
    elif component in ['storage', 'iam', 'lock']:
        return 1 if comp_data.get('status') == 'connected' else 0
    
    return -1

def cmd_discover_buckets(config):
    data = get_data(config)
    buckets = data.get('buckets', [])
    
    lld_data = []
    for bucket in buckets:
        lld_data.append({
            '{#BUCKET_NAME}': bucket['name']
        })
    
    return json.dumps({'data': lld_data})

def cmd_bucket(config, bucket_name, metric):
    data = get_data(config)
    buckets = data.get('buckets', [])
    
    for bucket in buckets:
        if bucket['name'] == bucket_name:
            if metric == 'objects':
                return bucket['objects']
            elif metric == 'bytes':
                return bucket['bytes']
            elif metric == 'age':
                if bucket.get('last_modified'):
                    try:
                        modified = datetime.fromisoformat(bucket['last_modified'].replace('Z', '+00:00'))
                        age = time.time() - modified.timestamp()
                        return int(age)
                    except:
                        pass
                return -1
    
    return -1

def cmd_capacity(config, metric):
    data = get_data(config)
    disk = data.get('disk', {})
    
    if metric == 'used':
        return disk.get('used_bytes', 0)
    elif metric == 'total':
        return disk.get('total_bytes', 0)
    elif metric == 'pct':
        return disk.get('used_pct', 0)
    
    return -1

def main():
    if len(sys.argv) < 2:
        print("Usage: lt_rustfs.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    
    config = load_config()
    cmd = sys.argv[1]
    
    if cmd == 'ping':
        print(cmd_ping(config))
    elif cmd == 'health':
        if len(sys.argv) < 3:
            print("Usage: lt_rustfs.py health <status|ready|version>", file=sys.stderr)
            sys.exit(1)
        print(cmd_health(config, sys.argv[2]))
    elif cmd == 'cluster':
        if len(sys.argv) < 3:
            print("Usage: lt_rustfs.py cluster <status|ready|storage|iam|lock>", file=sys.stderr)
            sys.exit(1)
        print(cmd_cluster(config, sys.argv[2]))
    elif cmd == 'discover':
        if len(sys.argv) < 3:
            print("Usage: lt_rustfs.py discover buckets", file=sys.stderr)
            sys.exit(1)
        if sys.argv[2] == 'buckets':
            print(cmd_discover_buckets(config))
        else:
            print(f"Unknown discovery type: {sys.argv[2]}", file=sys.stderr)
            sys.exit(1)
    elif cmd == 'bucket':
        if len(sys.argv) < 4:
            print("Usage: lt_rustfs.py bucket <name> <objects|bytes|age>", file=sys.stderr)
            sys.exit(1)
        print(cmd_bucket(config, sys.argv[2], sys.argv[3]))
    elif cmd == 'capacity':
        if len(sys.argv) < 3:
            print("Usage: lt_rustfs.py capacity <used|total|pct>", file=sys.stderr)
            sys.exit(1)
        print(cmd_capacity(config, sys.argv[2]))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
