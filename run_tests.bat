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
    echo Running all tests with coverage...
    pytest tests/ -v --tb=short
    if errorlevel 1 exit /b 1
    
    echo.
    echo Generating coverage report...
    pytest tests/ --cov=server --cov=app --cov-report=html --cov-report=term-missing
    
    echo.
    echo ? Coverage report generated in htmlcov/index.html
    echo Open with: start htmlcov\index.html
) else if "%1"=="quick" (
    echo Running quick tests (stop on first failure)...
    pytest tests/ -v --tb=short -x
) else if "%1"=="unit" (
    echo Running unit tests only...
    pytest tests/ -v -m unit
) else if "%1"=="integration" (
    echo Running integration tests only...
    pytest tests/ -v -m integration
) else if "%1"=="coverage" (
    echo Running tests with coverage...
    pytest tests/ --cov=server --cov=app --cov-report=html --cov-report=term-missing
    echo.
    echo ? Coverage report: htmlcov\index.html
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
