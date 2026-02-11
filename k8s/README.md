# Kubernetes Stack (Song song Docker Compose)

This folder provides a Kubernetes manifest to run the same infrastructure services as the Docker Compose stack. It is intended for local development with kind or minikube.

## Requirements

- kubectl
- Local Kubernetes cluster (kind or minikube)

## Quick Start (kind)

```bash
kind create cluster --name nexus-data-platform
docker build -t nexus-api:local -f apps/api/Dockerfile .
docker build -t nexus-frontend:local \
	--build-arg VITE_API_URL=http://localhost:8000 \
	-f apps/frontend/Dockerfile .
kind load docker-image nexus-api:local --name nexus-data-platform
kind load docker-image nexus-frontend:local --name nexus-data-platform
kubectl apply -f k8s/stack.yaml
kubectl -n nexus-data-platform get pods
```

## Port Forwarding

```bash
kubectl -n nexus-data-platform port-forward svc/airflow-webserver 8888:8888
kubectl -n nexus-data-platform port-forward svc/minio 9000:9000
kubectl -n nexus-data-platform port-forward svc/minio 9001:9001
kubectl -n nexus-data-platform port-forward svc/clickhouse 8123:8123
kubectl -n nexus-data-platform port-forward svc/redis 6379:6379
kubectl -n nexus-data-platform port-forward svc/postgres 5432:5432
kubectl -n nexus-data-platform port-forward svc/superset 8088:8088
kubectl -n nexus-data-platform port-forward svc/trino 8081:8081
kubectl -n nexus-data-platform port-forward svc/api 8000:8000
kubectl -n nexus-data-platform port-forward svc/frontend 3000:3000
```

## Kafka External Access

The manifest exposes a NodePort for Kafka at port 30092. For local access with kind or minikube:

```bash
kubectl -n nexus-data-platform get svc kafka-external
```

If NodePort is not reachable, use port-forward instead:

```bash
kubectl -n nexus-data-platform port-forward svc/kafka 9092:9092
```

## Notes

- The Airflow DAG ConfigMap in [k8s/stack.yaml](./stack.yaml) is a minimal stub for local validation.
- To load the full DAG, replace the ConfigMap with a generated one:

```bash
kubectl -n nexus-data-platform create configmap airflow-dags \
	--from-file=pipelines/airflow/dags/tourism_events_pipeline.py \
	--dry-run=client -o yaml | kubectl apply -f -
```

- The shared event schema is mounted to `/opt/packages/shared/schemas/event.schema.json` for the DAG.
- API and frontend are deployed as local images: `nexus-api:local`, `nexus-frontend:local`.

## Cleanup

```bash
kubectl delete -f k8s/stack.yaml
kind delete cluster --name nexus-data-platform
```
