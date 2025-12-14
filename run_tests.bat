@echo off
REM Windows batch script to run tests for Custom Steam Dashboard

echo ??????????????????????????????????????????????????????????????
echo ?     Custom Steam Dashboard - Test Runner (Windows)        ?
echo ??????????????????????????????????????????????????????????????
echo.

REM Check if pytest is installed
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo ? pytest not installed!
    echo Install with: pip install -r requirements-test.txt
    exit /b 1
)

REM Parse command line arguments
if "%1"=="" (
    echo Running all tests sequentially with coverage...
    echo.

    REM Clear previous coverage
    del .coverage 2>nul

    echo Running: Unit Tests...
    pytest tests/unit/ -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 1 /nobreak >nul

    echo.
    echo Running: Integration - API Endpoints...
    pytest tests/integration/server/test_api_endpoints.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 2 /nobreak >nul

    echo.
    echo Running: Integration - Scheduler...
    pytest tests/integration/server/test_scheduler.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 2 /nobreak >nul

    echo.
    echo Running: Integration - Database...
    pytest tests/integration/server/test_database_integration.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 3 /nobreak >nul

    echo.
    echo Running: Integration - Async Client...
    pytest tests/integration/app/test_async_real_integration.py -v --cov=server --cov=app --cov-append --cov-report=

    echo.
    echo Generating combined coverage report...
    python -m coverage html
    python -m coverage report

    echo.
    echo Coverage report generated in htmlcov\index.html
    echo Open with: start htmlcov\index.html
) else if "%1"=="quick" (
    echo Running quick tests (stop on first failure)...
    pytest tests/ -v --tb=short -x
) else if "%1"=="unit" (
    echo Running unit tests only...
    pytest tests/unit/ -v
) else if "%1"=="integration" (
    echo Running integration tests sequentially...
    echo.

    del .coverage 2>nul

    echo Running: API Endpoints...
    pytest tests/integration/server/test_api_endpoints.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 2 /nobreak >nul

    echo.
    echo Running: Scheduler...
    pytest tests/integration/server/test_scheduler.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 2 /nobreak >nul

    echo.
    echo Running: Database Integration...
    pytest tests/integration/server/test_database_integration.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 3 /nobreak >nul

    echo.
    echo Running: Async Client...
    pytest tests/integration/app/test_async_real_integration.py -v --cov=server --cov=app --cov-append --cov-report=

    python -m coverage html
    python -m coverage report
) else if "%1"=="coverage" (
    echo Running tests sequentially with detailed coverage...
    echo.

    del .coverage 2>nul

    pytest tests/unit/ -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 1 /nobreak >nul
    pytest tests/integration/server/test_api_endpoints.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 2 /nobreak >nul
    pytest tests/integration/server/test_scheduler.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 2 /nobreak >nul
    pytest tests/integration/server/test_database_integration.py -v --cov=server --cov=app --cov-append --cov-report=
    timeout /t 3 /nobreak >nul
    pytest tests/integration/app/test_async_real_integration.py -v --cov=server --cov=app --cov-append --cov-report=

    python -m coverage html
    python -m coverage report

    echo.
    echo Coverage report: htmlcov\index.html
    start htmlcov\index.html
) else (
    echo Running pytest with custom arguments...
    pytest %*
)

if errorlevel 1 (
    echo.
    echo ? Some tests failed!
    exit /b 1
) else (
    echo.
    echo ? All tests passed!
    exit /b 0
)
