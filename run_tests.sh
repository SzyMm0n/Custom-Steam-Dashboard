#!/bin/bash
# Test runner script for Custom Steam Dashboard

echo "======================================================================"
echo "     Custom Steam Dashboard - Test Runner"
echo "======================================================================"
echo ""

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not installed!"
    echo "Install with: pip install -r requirements-test.txt"
    exit 1
fi

   # Parse arguments
if [ $# -eq 0 ]; then
    echo "Running all tests sequentially with coverage..."
    echo ""

    # Clear previous coverage data
    rm -f .coverage

    # Run unit tests first (fast)
    echo "🧪 Running: Unit Tests..."
    pytest tests/unit/ -v --cov=server --cov=app --cov-append --cov-report=
    sleep 1

    # Run integration tests sequentially
    echo ""
    echo "🧪 Running: Integration - API Endpoints..."
    pytest tests/integration/server/test_api_endpoints.py -v --cov=server --cov=app --cov-append --cov-report=
    sleep 2

    echo ""
    echo "🧪 Running: Integration - Scheduler..."
    pytest tests/integration/server/test_scheduler.py -v --cov=server --cov=app --cov-append --cov-report=
    sleep 2

    echo ""
    echo "🧪 Running: Integration - Database..."
    pytest tests/integration/server/test_database_integration.py -v --cov=server --cov=app --cov-append --cov-report=
    sleep 3

    echo ""
    echo "🧪 Running: Integration - Async Client..."
    pytest tests/integration/app/test_async_real_integration.py -v --cov=server --cov=app --cov-append --cov-report=

    # Generate final coverage report
    echo ""
    echo "📊 Generating combined coverage report..."
    python -m coverage html
    python -m coverage report

    echo ""
    echo "✅ Coverage report generated in htmlcov/index.html"
    echo "Open with: open htmlcov/index.html (Mac) or xdg-open htmlcov/index.html (Linux)"
elif [ "$1" = "quick" ]; then
    echo "Running quick tests (stop on first failure)..."
    pytest tests/ -p no:qt -v --tb=short -x
elif [ "$1" = "unit" ]; then
    echo "Running unit tests only..."
    pytest tests/unit/ -v
elif [ "$1" = "integration" ]; then
    echo "Running integration tests sequentially (to avoid resource conflicts)..."
    echo ""

    # Clear previous coverage data
    rm -f .coverage

    # Counter for results
    TOTAL_PASSED=0
    TOTAL_FAILED=0

    # Run each integration test file separately with delays
    echo "🧪 Running: API Endpoints..."
    pytest tests/integration/server/test_api_endpoints.py -v --cov=server --cov=app --cov-append --cov-report=
    RESULT=$?
    [ $RESULT -eq 0 ] && TOTAL_PASSED=$((TOTAL_PASSED + 1)) || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    sleep 2

    echo ""
    echo "🧪 Running: Scheduler Tests..."
    pytest tests/integration/server/test_scheduler.py -v --cov=server --cov=app --cov-append --cov-report=
    RESULT=$?
    [ $RESULT -eq 0 ] && TOTAL_PASSED=$((TOTAL_PASSED + 1)) || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    sleep 2

    echo ""
    echo "🧪 Running: Database Integration..."
    pytest tests/integration/server/test_database_integration.py -v --cov=server --cov=app --cov-append --cov-report=
    RESULT=$?
    [ $RESULT -eq 0 ] && TOTAL_PASSED=$((TOTAL_PASSED + 1)) || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    sleep 3

    echo ""
    echo "🧪 Running: Async Client Integration..."
    pytest tests/integration/app/test_async_real_integration.py -v --cov=server --cov=app --cov-append --cov-report=
    RESULT=$?
    [ $RESULT -eq 0 ] && TOTAL_PASSED=$((TOTAL_PASSED + 1)) || TOTAL_FAILED=$((TOTAL_FAILED + 1))

    # Generate final coverage report
    echo ""
    echo "📊 Generating combined coverage report..."
    pytest --cov=server --cov=app --cov-report=html --cov-report=term-missing tests/integration/ --collect-only > /dev/null 2>&1 || true

    echo ""
    echo "✅ Integration test groups completed: $TOTAL_PASSED passed, $TOTAL_FAILED failed"
elif [ "$1" = "coverage" ]; then
    echo "Running tests sequentially with detailed coverage..."
    echo ""

    # Clear previous coverage data
    rm -f .coverage

    # Run all test groups
    pytest tests/unit/ -v --cov=server --cov=app --cov-append --cov-report=
    sleep 1
    pytest tests/integration/server/test_api_endpoints.py -v --cov=server --cov=app --cov-append --cov-report=
    sleep 2
    pytest tests/integration/server/test_scheduler.py -v --cov=server --cov=app --cov-append --cov-report=
    sleep 2
    pytest tests/integration/server/test_database_integration.py -v --cov=server --cov=app --cov-append --cov-report=
    sleep 3
    pytest tests/integration/app/test_async_real_integration.py -v --cov=server --cov=app --cov-append --cov-report=

    # Generate reports
    python -m coverage html
    python -m coverage report

    echo ""
    echo "✅ Coverage report: htmlcov/index.html"

    # Try to open coverage report
    if command -v open &> /dev/null; then
        open htmlcov/index.html
    elif command -v xdg-open &> /dev/null; then
        xdg-open htmlcov/index.html
    fi
else
    echo "Running pytest with custom arguments (adding -p no:qt)..."
    pytest -p no:qt "$@"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "? All tests passed!"
    exit 0
else
    echo ""
    echo "? Some tests failed!"
    exit 1
fi
