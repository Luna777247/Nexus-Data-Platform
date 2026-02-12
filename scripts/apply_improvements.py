#!/usr/bin/env python3
"""
Script to add health checks and resource limits to all services
Cập nhật docker-compose-production.yml với health checks và memory limits
"""

import yaml
import sys
from pathlib import Path

def add_healthcheck_and_limits():
    """Thêm health checks và memory limits vào docker-compose"""
    
    compose_file = Path("/workspaces/Nexus-Data-Platform/infra/docker-stack/docker-compose-production.yml")
    
    with open(compose_file, 'r') as f:
        content = yaml.safe_load(f)
    
    services = content.get('services', {})
    
    # Health check templates
    healthchecks = {
        'kafka-2': {
            'test': 'kafka-broker-api-versions --bootstrap-server localhost:9093',
            'interval': '10s',
            'timeout': '10s',
            'retries': 5
        },
        'kafka-3': {
            'test': 'kafka-broker-api-versions --bootstrap-server localhost:9094',
            'interval': '10s',
            'timeout': '10s',
            'retries': 5
        },
        'schema-registry': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8081/subjects'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 3
        },
        'spark-stream-master': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8080/json/'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 3
        },
        'spark-stream-worker-1': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8081/'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 3
        },
        'spark-stream-worker-2': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8081/'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 3
        },
        'spark-batch-master': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8082/json/'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 3
        },
        'spark-batch-worker-1': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8081/'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 3
        },
        'spark-batch-worker-2': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8081/'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 3
        },
        'postgres-iceberg': {
            'test': ['CMD-SHELL', 'pg_isready -U iceberg'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 5,
            'start_period': '10s'
        },
        'minio-2': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:9000/minio/health/live'],
            'interval': '30s',
            'timeout': '20s',
            'retries': 3
        },
        'minio-3': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:9000/minio/health/live'],
            'interval': '30s',
            'timeout': '20s',
            'retries': 3
        },
        'minio-4': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:9000/minio/health/live'],
            'interval': '30s',
            'timeout': '20s',
            'retries': 3
        },
        'data-quality': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8000/'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 3,
            'start_period': '30s'
        },
        'openmetadata': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8585/'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 3,
            'start_period': '60s'
        },
        'prometheus': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:9090/-/healthy'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 3
        },
        'grafana': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:3000/api/health'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 3,
            'start_period': '30s'
        },
        'kafka-exporter': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:9308/'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 3
        },
        'clickhouse': {
            'test': ['CMD', 'wget', '--quiet', '--tries=1', '--spider', 'http://localhost:8123/ping'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 3,
            'start_period': '30s'
        }
    }
    
    # Resource limits per service
    limits = {
        'zookeeper': {'memory': '1.5G', 'cpus': '1', 'reserve_memory': '1G', 'reserve_cpus': '0.5'},
        'kafka-1': {'memory': '2G', 'cpus': '1', 'reserve_memory': '1.5G', 'reserve_cpus': '0.5'},
        'kafka-2': {'memory': '2G', 'cpus': '1', 'reserve_memory': '1.5G', 'reserve_cpus': '0.5'},
        'kafka-3': {'memory': '2G', 'cpus': '1', 'reserve_memory': '1.5G', 'reserve_cpus': '0.5'},
        'schema-registry': {'memory': '1G', 'cpus': '0.5', 'reserve_memory': '768M', 'reserve_cpus': '0.25'},
        'spark-stream-master': {'memory': '2G', 'cpus': '2', 'reserve_memory': '1.5G', 'reserve_cpus': '1'},
        'spark-stream-worker-1': {'memory': '2G', 'cpus': '2', 'reserve_memory': '1.5G', 'reserve_cpus': '1'},
        'spark-stream-worker-2': {'memory': '2G', 'cpus': '2', 'reserve_memory': '1.5G', 'reserve_cpus': '1'},
        'spark-batch-master': {'memory': '4G', 'cpus': '4', 'reserve_memory': '3G', 'reserve_cpus': '2'},
        'spark-batch-worker-1': {'memory': '4G', 'cpus': '4', 'reserve_memory': '3G', 'reserve_cpus': '2'},
        'spark-batch-worker-2': {'memory': '4G', 'cpus': '4', 'reserve_memory': '3G', 'reserve_cpus': '2'},
        'postgres-iceberg': {'memory': '2G', 'cpus': '2', 'reserve_memory': '1.5G', 'reserve_cpus': '1'},
        'minio-1': {'memory': '1.5G', 'cpus': '1', 'reserve_memory': '1G', 'reserve_cpus': '0.5'},
        'minio-2': {'memory': '1.5G', 'cpus': '1', 'reserve_memory': '1G', 'reserve_cpus': '0.5'},
        'minio-3': {'memory': '1.5G', 'cpus': '1', 'reserve_memory': '1G', 'reserve_cpus': '0.5'},
        'minio-4': {'memory': '1.5G', 'cpus': '1', 'reserve_memory': '1G', 'reserve_cpus': '0.5'},
        'data-quality': {'memory': '1G', 'cpus': '0.5', 'reserve_memory': '768M', 'reserve_cpus': '0.25'},
        'openmetadata': {'memory': '2G', 'cpus': '1', 'reserve_memory': '1.5G', 'reserve_cpus': '0.5'},
        'prometheus': {'memory': '1G', 'cpus': '1', 'reserve_memory': '512M', 'reserve_cpus': '0.5'},
        'grafana': {'memory': '1G', 'cpus': '1', 'reserve_memory': '512M', 'reserve_cpus': '0.5'},
        'kafka-exporter': {'memory': '512M', 'cpus': '0.5', 'reserve_memory': '256M', 'reserve_cpus': '0.25'},
        'clickhouse': {'memory': '2G', 'cpus': '2', 'reserve_memory': '1.5G', 'reserve_cpus': '1'},
    }
    
    updated_services = {}
    
    for service_name, service_config in services.items():
        # Add healthcheck if defined
        if service_name in healthchecks:
            hc = healthchecks[service_name]
            service_config['healthcheck'] = hc
            print(f"✅ Added healthcheck to {service_name}")
        
        # Add resource limits
        if service_name in limits:
            lim = limits[service_name]
            if 'deploy' not in service_config:
                service_config['deploy'] = {}
            if 'resources' not in service_config['deploy']:
                service_config['deploy']['resources'] = {}
            
            service_config['deploy']['resources']['limits'] = {
                'memory': lim['memory'],
                'cpus': lim['cpus']
            }
            service_config['deploy']['resources']['reservations'] = {
                'memory': lim['reserve_memory'],
                'cpus': lim['reserve_cpus']
            }
            print(f"✅ Added resource limits to {service_name}: {lim['memory']} memory, {lim['cpus']} CPU")
        
        updated_services[service_name] = service_config
    
    content['services'] = updated_services
    
    # Write back to file
    with open(compose_file, 'w') as f:
        yaml.dump(content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"\n✅ Updated {compose_file} successfully!")
    print(f"📊 Added health checks and resource limits to {len([s for s in healthchecks if s in services])} services")
    
    return content

if __name__ == '__main__':
    try:
        add_healthcheck_and_limits()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
