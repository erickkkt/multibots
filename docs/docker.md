# Docker Quick Start

This project runs with Docker Compose using three services:

- Frontend (Angular, served by Nginx)
- Backend API (.NET)
- PostgreSQL

## Prerequisites

- Docker Desktop installed
- Docker Desktop running

## Start / Stop (recommended scripts)

From repository root:

### macOS / Linux

```bash
chmod +x ./docker.sh
./docker.sh up
```

### Windows (Command Prompt)

```bat
docker.bat up
```

Common commands:

- `up`: build + start all services
- `down`: stop + remove services
- `logs`: follow logs
- `rebuild`: rebuild from scratch and start

## Fallback (without scripts)

If your Docker supports Compose v2:

```bash
docker compose up -d --build
```

If using legacy Compose v1:

```bash
docker-compose up -d --build
```

## Service URLs and ports

- Frontend: http://localhost:4200
- API: http://localhost:5238
- API health: http://localhost:5238/health
- PostgreSQL: localhost:5432

## Environment values used in Compose

API container uses:

- `ASPNETCORE_ENVIRONMENT=Development`
- `ConnectionStrings__DefaultConnection=Host=postgres;Port=5432;Database=multibots;Username=multibots;Password=multibots`
- `PythonEngine__BaseUrl=http://host.docker.internal:8000`

Postgres container uses:

- `POSTGRES_DB=multibots`
- `POSTGRES_USER=multibots`
- `POSTGRES_PASSWORD=multibots`

## First run notes

- Database schema migrations are applied automatically when the API starts.
- First startup can take longer while Docker pulls base images.

## Troubleshooting

### Docker is installed but script says daemon is not running

Start Docker Desktop, wait until it shows as running, then retry.

### Port already in use (4200, 5238, or 5432)

Stop conflicting local services or update mapped ports in `docker-compose.yml`.

### API cannot connect to Postgres

1. Check Postgres health and logs:
   - `./docker.sh logs` or `docker.bat logs`
2. Ensure `ConnectionStrings__DefaultConnection` still points to host `postgres`.
3. Restart stack:
   - `./docker.sh down && ./docker.sh up`

### `docker compose` command not found

- Script automatically falls back to `docker-compose` if available.
- If neither exists, install/upgrade Docker Desktop.

### API endpoints fail because Python engine is unavailable

The API expects a Python engine at `http://host.docker.internal:8000`. Run the Python engine locally on that port, or update `PythonEngine__BaseUrl` in `docker-compose.yml`.
