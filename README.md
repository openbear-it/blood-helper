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
