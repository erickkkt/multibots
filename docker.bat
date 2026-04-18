@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker is not installed or not available in PATH.
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker daemon is not running. Start Docker Desktop and try again.
  exit /b 1
)

docker compose version >nul 2>&1
if not errorlevel 1 (
  set "COMPOSE_CMD=docker compose"
) else (
  docker-compose version >nul 2>&1
  if errorlevel 1 (
    echo Docker Compose was not found. Install Docker Compose v2 or v1.
    exit /b 1
  )
  set "COMPOSE_CMD=docker-compose"
)

if "%~1"=="" goto usage

if /I "%~1"=="up" (
  %COMPOSE_CMD% up -d --build
  exit /b %errorlevel%
)

if /I "%~1"=="down" (
  %COMPOSE_CMD% down --remove-orphans
  exit /b %errorlevel%
)

if /I "%~1"=="logs" (
  %COMPOSE_CMD% logs -f --tail=200
  exit /b %errorlevel%
)

if /I "%~1"=="rebuild" (
  %COMPOSE_CMD% build --no-cache
  if errorlevel 1 exit /b %errorlevel%
  %COMPOSE_CMD% up -d
  exit /b %errorlevel%
)

:usage
echo Usage: docker.bat ^<command^>
echo.
echo Commands:
echo   up       Build and start all services in background
echo   down     Stop and remove services
echo   logs     Follow service logs
echo   rebuild  Rebuild images with no cache and start services
exit /b 1
