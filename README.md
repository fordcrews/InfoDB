# InfoDB

Modern network asset inventory — a rewrite of the legacy IADB PHP application.

## Stack

- **API:** FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT auth
- **Web:** React, TypeScript, Vite, TanStack Query
- **Discovery:** SNMP ARP table walks (ipNetToMediaTable)

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Web UI: http://localhost:5173
- API docs: http://localhost:8000/docs
- Default login: `admin@local.dev` / value of `ADMIN_PASSWORD` in `.env`

## Features

### Implemented

- JWT authentication with admin/operator roles
- Asset dashboard with search, pagination, and subnet filter
- Agency, subnet, router, and SNMP profile management (admin)
- SNMP ARP discovery — walks routers and upserts assets by MAC address
- Discovery run history with per-router stats
- Asset detail page with manual enrichment (hostname, OS, subnet)
- Agency × OS breakdown on dashboard

### Roadmap (from legacy IADB)

- Scheduled discovery (cron/APScheduler)
- Port scanning
- Owner/IASO/SA assignment workflow
- LDAP authentication
- Data migration from `iadb` SQLite
- Extended asset fields (building, room, barcode, DC flags)

## Discovery workflow

1. Create an **SNMP profile** (v2c community or v3 credentials)
2. Add a **router** with IP and link it to the profile
3. Define **subnets** (CIDRs) — assets are auto-matched by IP
4. Go to **Discovery** and run an ARP walk
5. View/update discovered assets on the dashboard

SNMP passwords are encrypted at rest using a key derived from `JWT_SECRET`.

## Project layout

```
InfoDB/
├── api/           FastAPI backend
├── web/           React frontend
├── docker-compose.yml
└── .env.example
```

## Development

API and web both hot-reload inside Docker. The API runs migrations and seeds sample data on startup.

To seed manually:

```bash
docker compose exec api python -m scripts.seed
```