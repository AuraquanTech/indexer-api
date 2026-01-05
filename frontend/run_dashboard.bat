@echo off
title Indexer Dashboard
echo Starting Indexer Dashboard...
echo based at: %~dp0

cd /d "%~dp0"

:: Check if build exists, if not build it
if not exist ".next" (
    echo Build not found. Building application...
    call npm run build
)

echo Detecting available port...
for /f "tokens=*" %%i in ('node scripts/find-port.js') do set ALLOCATED_PORT=%%i

if "%ALLOCATED_PORT%"=="" (
    echo [31mError: Could not allocate a port. Check scripts/find-port.js output. [0m
    pause
    exit /b 1
)

echo Port %ALLOCATED_PORT% allocated.
echo.
echo Starting Indexer Dashboard on port %ALLOCATED_PORT%...

start "" "http://localhost:%ALLOCATED_PORT%"
call npx next start -p %ALLOCATED_PORT%
