#!/bin/bash
# Build script for Custom Steam Dashboard executable
# This script creates a standalone executable for the desktop application

set -e  # Exit on error

echo "=========================================="
echo "Custom Steam Dashboard - Build Executable"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [ ! -f "steam_dashboard.spec" ]; then
    echo -e "${RED}Error: steam_dashboard.spec not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: No virtual environment detected.${NC}"
    echo -e "${YELLOW}It's recommended to build in a virtual environment.${NC}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clean previous builds
echo -e "${YELLOW}[1/4] Cleaning previous builds...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ Clean complete${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}[2/4] Checking dependencies...${NC}"
python3 -c "import PyInstaller" 2>/dev/null || {
    echo -e "${RED}PyInstaller not found. Installing...${NC}"
    pip install pyinstaller>=6.9
}
echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Build executable
echo -e "${YELLOW}[3/4] Building executable...${NC}"
echo "This may take a few minutes..."
echo ""
pyinstaller --clean steam_dashboard.spec

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Build successful!${NC}"
else
    echo ""
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi
echo ""

# Display results
echo -e "${YELLOW}[4/4] Build complete!${NC}"
echo ""
echo "=========================================="
echo "Build Summary"
echo "=========================================="
echo ""

if [ -d "dist" ]; then
    echo -e "${GREEN}Executable location:${NC}"
    echo "  $(pwd)/dist/"
    echo ""
    echo "Files created:"
    ls -lh dist/
    echo ""
    echo -e "${YELLOW}Note:${NC}"
    echo "  - Make sure the backend server is running before launching the app"
    echo "  - Default server URL: http://localhost:8000"
    echo "  - You can distribute the entire 'dist' folder or just the executable"
    echo ""
    echo -e "${GREEN}To run the application:${NC}"
    if [ "$(uname)" == "Darwin" ]; then
        echo "  open dist/SteamDashboard.app"
    else
        echo "  ./dist/SteamDashboard"
    fi
else
    echo -e "${RED}Error: dist directory not found!${NC}"
    exit 1
fi

echo ""
echo "=========================================="

