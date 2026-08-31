#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LT RustFS Collector - Lidorio-Zabbix-Pack v0.7.0 (lib_lt refactor)
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

# Import lib_lt
sys.path.insert(0, "/etc/zabbix/lib")
try:
    import lib_lt
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
    import lib_lt

LOG = lib_lt.get_logger("rustfs")

CACHE_FILE = "/tmp/lt_rustfs.cache.json"
CACHE_TTL = 120
ALIAS_NAME = "rustfs_zabbix"

def load_config():
    """Load config using lib_lt, with RustFS-specific defaults."""
    defaults = {
        "endpoint": "http://127.0.0.1:9000",
        "access_key": "",
        "secret_key": "",
        "data_path": "/data/rustfs/mnmd"
    }
    return lib_lt.load_config("/etc/zabbix/scripts/lt_rustfs.conf", defaults)

def ensure_alias(config):
    cmd = f'rc alias set {ALIAS_NAME} {config["endpoint"]} "{config["access_key"]}" "{config["secret_key"]}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        LOG.info("rc alias configured successfully")
        return True
    LOG.error(f"rc alias failed: {result.stderr}")
    return False

def get_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        if time.time() - cache.get('timestamp', 0) < CACHE_TTL:
            LOG.info("cache hit")
            return cache
    except Exception as e:
        LOG.warning(f"cache read error: {e}")
    return None

def save_cache(data):
    try:
        cache = {'timestamp': time.time(), 'data': data}
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
        LOG.info("cache saved")
    except Exception as e:
        LOG.warning(f"cache write error: {e}")

def fetch_health(endpoint):
    try:
        url = f"{endpoint}/health"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        LOG.error(f"health fetch failed: {e}")
        return None

def fetch_cluster_health(endpoint):
    try:
        url = f"{endpoint}/minio/health/cluster"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        LOG.error(f"cluster health fetch failed: {e}")
        return None

def run_rc_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout
        LOG.error(f"rc command failed: {cmd} -> {result.stderr}")
        return None
    except subprocess.TimeoutExpired:
        LOG.error(f"rc command timeout: {cmd}")
        return None
    except Exception as e:
        LOG.error(f"rc command error: {cmd} -> {e}")
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
        LOG.info(f"collected {len(buckets)} buckets")
        return buckets
    except Exception as e:
        LOG.error(f"bucket collection parse error: {e}")
        return []

def collect_bucket_size(config, bucket_name):
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
    except Exception as e:
        LOG.error(f"bucket size parse error for {bucket_name}: {e}")
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
    
    LOG.info(f"disk: used={result['used_bytes']} total={result['total_bytes']} pct={result['used_pct']}%")
    return result

def collect_all(config):
    LOG.info("starting full collection")
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
    
    LOG.info(f"collection complete: {len(data['buckets'])} buckets")
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
    result = 1 if health and health.get('status') == 'ok' else 0
    LOG.info(f"ping: {result}")
    return result

def cmd_health(config, key):
    data = get_data(config)
    health = data.get('health', {})
    if not health:
        LOG.error("health data unavailable")
        return -1
    
    if key == 'status':
        return 1 if health.get('status') == 'ok' else 0
    elif key == 'ready':
        return 1 if health.get('ready') else 0
    elif key == 'version':
        return health.get('version', 'unknown')
    
    LOG.error(f"unknown health key: {key}")
    return -1

def cmd_cluster(config, component):
    data = get_data(config)
    cluster = data.get('cluster', {})
    if not cluster:
        LOG.error("cluster data unavailable")
        return -1
    
    details = cluster.get('details', {})
    comp_data = details.get(component, {})
    
    if component == 'status':
        return 1 if cluster.get('status') == 'ok' else 0
    elif component == 'ready':
        return 1 if cluster.get('ready') else 0
    elif component in ['storage', 'iam', 'lock']:
        return 1 if comp_data.get('status') == 'connected' else 0
    
    LOG.error(f"unknown cluster component: {component}")
    return -1

def cmd_discover_buckets(config):
    data = get_data(config)
    buckets = data.get('buckets', [])
    
    lld_data = []
    for bucket in buckets:
        lld_data.append({
            '{#BUCKET_NAME}': bucket['name']
        })
    
    LOG.info(f"discover buckets: {len(lld_data)}")
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
                    except Exception as e:
                        LOG.error(f"age calculation error for {bucket_name}: {e}")
                return -1
    
    LOG.warning(f"bucket not found: {bucket_name}")
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
    
    LOG.error(f"unknown capacity metric: {metric}")
    return -1

def main():
    if len(sys.argv) < 2:
        lib_lt.log("ERROR", "no command provided", name="rustfs")
        lib_lt.emit("Usage: lt_rustfs.py <command> [args]", exit_code=1)
    
    config = load_config()
    cmd = sys.argv[1]
    
    try:
        if cmd == 'ping':
            lib_lt.emit(cmd_ping(config))
        elif cmd == 'health':
            if len(sys.argv) < 3:
                lib_lt.emit("Usage: lt_rustfs.py health <status|ready|version>", exit_code=1)
            lib_lt.emit(cmd_health(config, sys.argv[2]))
        elif cmd == 'cluster':
            if len(sys.argv) < 3:
                lib_lt.emit("Usage: lt_rustfs.py cluster <status|ready|storage|iam|lock>", exit_code=1)
            lib_lt.emit(cmd_cluster(config, sys.argv[2]))
        elif cmd == 'discover':
            if len(sys.argv) < 3:
                lib_lt.emit("Usage: lt_rustfs.py discover buckets", exit_code=1)
            if sys.argv[2] == 'buckets':
                lib_lt.emit(cmd_discover_buckets(config))
            else:
                lib_lt.emit(f"Unknown discovery type: {sys.argv[2]}", exit_code=1)
        elif cmd == 'bucket':
            if len(sys.argv) < 4:
                lib_lt.emit("Usage: lt_rustfs.py bucket <name> <objects|bytes|age>", exit_code=1)
            lib_lt.emit(cmd_bucket(config, sys.argv[2], sys.argv[3]))
        elif cmd == 'capacity':
            if len(sys.argv) < 3:
                lib_lt.emit("Usage: lt_rustfs.py capacity <used|total|pct>", exit_code=1)
            lib_lt.emit(cmd_capacity(config, sys.argv[2]))
        else:
            LOG.error(f"unknown command: {cmd}")
            lib_lt.emit(f"Unknown command: {cmd}", exit_code=1)
    except Exception as e:
        LOG.error(f"unhandled exception: {e}", exc_info=True)
        lib_lt.emit(-1, exit_code=1)

if __name__ == '__main__':
    main()
