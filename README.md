# blood-helper Intelligence Platform

A production-ready platform for blood inventory monitoring, consumption forecasting, wastage analysis, and donation campaign management.

## Architecture

```
blood-helper/
├── backend/                  # FastAPI + Python 3.12
│   ├── app/
│   │   ├── domain/           # Domain models & repository interfaces (DDD)
│   │   │   ├── blood_inventory/
│   │   │   └── forecasting/
│   │   ├── infrastructure/   # DB, cache, messaging implementations
│   │   │   ├── database/
│   │   │   ├── cache/
│   │   │   ├── messaging/
│   │   │   └── repositories/
│   │   ├── application/      # Services, ML forecasters, Celery tasks
│   │   │   ├── ml/
│   │   │   ├── services/
│   │   │   └── tasks/
│   │   └── api/              # FastAPI routers + WebSocket
│   │       ├── v1/
│   │       └── websocket/
│   ├── alembic/              # DB migrations
│   └── tests/                # Unit + integration tests
└── frontend/                 # React + TypeScript + MUI
    └── src/
        ├── pages/
        ├── components/
        ├── hooks/
        ├── services/
        └── types/
```

## Deployment (k3s / Kubernetes)

### Prerequisites

- k3s cluster running (includes Traefik ingress + `local-path` StorageClass by default)
- Container registry accessible from the cluster
- `kubectl` configured to target the cluster

### Build & Push Images

```bash
# Backend
docker build -t your-registry/blood-helper-backend:latest ./backend
docker push your-registry/blood-helper-backend:latest

# Frontend
docker build -t your-registry/blood-helper-frontend:latest ./frontend
docker push your-registry/blood-helper-frontend:latest
```

Update image references in `k8s/backend/deployment.yaml`, `k8s/celery/worker.yaml`, `k8s/celery/beat.yaml`, and `k8s/frontend/deployment.yaml` with your registry.

### Configure Secrets

```bash
# Copy the secret template and fill in real base64-encoded values
cp k8s/02-secret.example.yaml k8s/02-secret.yaml

# Encode a value:
echo -n 'your-password' | base64
```

Edit `k8s/02-secret.yaml` and replace the placeholder values.

### Deploy

```bash
# Apply all manifests via Kustomize
kubectl apply -k k8s/

# Or apply individually in order:
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/redis/
kubectl apply -f k8s/backend/migration-job.yaml

# Wait for migration to complete
kubectl -n blood-helper wait --for=condition=complete job/blood-helper-migrate --timeout=120s

kubectl apply -f k8s/backend/deployment.yaml -f k8s/backend/service.yaml -f k8s/backend/hpa.yaml
kubectl apply -f k8s/celery/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/ingress.yaml
```

### Expose via Ingress

The ingress is configured for host `blood-helper.local`. Update `k8s/ingress.yaml` with your actual domain, then add a DNS record (or `/etc/hosts` entry for local testing) pointing to the k3s node IP.

```bash
# Local testing — get k3s node IP
kubectl get nodes -o wide

# Add to /etc/hosts
echo "<NODE_IP> blood-helper.local" | sudo tee -a /etc/hosts
```

| Endpoint | URL |
|----------|-----|
| Frontend | http://blood-helper.local |
| API | http://blood-helper.local/api/v1 |
| Swagger UI | http://blood-helper.local/api/v1/docs |
| WebSocket | ws://blood-helper.local/ws/alerts |

### Running Tests (local)

```bash
cd backend
python -m pytest
```

## ML Forecasting

The platform uses an **Ensemble model** combining:
- **Prophet** — captures seasonality and trend
- **XGBoost** — learns lag features and rolling statistics

Forecasts are automatically triggered daily via Celery Beat, or manually via `POST /api/v1/hospitals/{id}/forecasts/run`.

## Features

- **Blood Inventory Monitoring** — Real-time tracking per hospital and blood type
- **Consumption Forecasting** — Daily/weekly/monthly predictions with confidence intervals
- **Wastage Analysis** — Track expired/contaminated units with cost estimation
- **Donation Campaigns** — Create and manage donation drives with progress tracking
- **WebSocket Alerts** — Real-time critical inventory and expiry alerts
- **Department Analytics** — Per-department consumption tracking
