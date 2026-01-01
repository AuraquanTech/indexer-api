@echo off
echo.
echo ========================================
echo   IndexerAPI - Starting Server
echo ========================================
echo.

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Run install.bat first.
)

REM Initialize database
echo Initializing database...
python -c "import asyncio; from indexer_api.db.base import init_db; asyncio.run(init_db())"

echo.
echo Starting API server at http://localhost:8000
echo Documentation: http://localhost:8000/docs
echo.

REM Start server with reload
uvicorn indexer_api.main:app --host 0.0.0.0 --port 8000 --reload
