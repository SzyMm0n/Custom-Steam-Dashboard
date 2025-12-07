#!/bin/bash
# Shell script to run tests for Custom Steam Dashboard

echo "??????????????????????????????????????????????????????????????"
echo "?     Custom Steam Dashboard - Test Runner (Linux/Mac)      ?"
echo "??????????????????????????????????????????????????????????????"
echo ""

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "? pytest not installed!"
    echo "Install with: pip install -r requirements-test.txt"
    exit 1
fi

# Parse command line arguments
if [ $# -eq 0 ]; then
    echo "Running all tests with coverage..."
    pytest tests/ -v --tb=short
    if [ $? -ne 0 ]; then exit 1; fi
    
    echo ""
    echo "Generating coverage report..."
    pytest tests/ --cov=server --cov=app --cov-report=html --cov-report=term-missing
    
    echo ""
    echo "? Coverage report generated in htmlcov/index.html"
    echo "Open with: open htmlcov/index.html (Mac) or xdg-open htmlcov/index.html (Linux)"
elif [ "$1" = "quick" ]; then
    echo "Running quick tests (stop on first failure)..."
    pytest tests/ -v --tb=short -x
elif [ "$1" = "unit" ]; then
    echo "Running unit tests only..."
    pytest tests/ -v -m unit
elif [ "$1" = "integration" ]; then
    echo "Running integration tests only..."
    pytest tests/ -v -m integration
elif [ "$1" = "coverage" ]; then
    echo "Running tests with coverage..."
    pytest tests/ --cov=server --cov=app --cov-report=html --cov-report=term-missing
    echo ""
    echo "? Coverage report: htmlcov/index.html"
    
    # Try to open coverage report
    if command -v open &> /dev/null; then
        open htmlcov/index.html
    elif command -v xdg-open &> /dev/null; then
        xdg-open htmlcov/index.html
    fi
else
    echo "Running pytest with custom arguments..."
    pytest "$@"
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
