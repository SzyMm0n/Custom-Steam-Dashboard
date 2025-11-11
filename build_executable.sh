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

    # Copy .env.example as .env to dist folder if it doesn't exist
    if [ ! -f "dist/.env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example dist/.env
            echo -e "${GREEN}✓ Created dist/.env from .env.example${NC}"
            echo -e "${YELLOW}⚠ IMPORTANT: Edit dist/.env with your credentials!${NC}"
            echo ""
        fi
    fi

    # Copy README_USER.md to dist folder
    if [ -f "README_USER.md" ]; then
        cp README_USER.md dist/
        echo -e "${GREEN}✓ Copied README_USER.md to dist/${NC}"
        echo ""
    fi

    echo "Files created:"
    ls -lh dist/
    echo ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo "  1. Edit dist/.env file with your settings:"
    echo "     - SERVER_URL (backend API URL)"
    echo "     - CLIENT_ID and CLIENT_SECRET (authentication)"
    echo "  2. Make sure these match your server configuration"
    echo ""
    echo -e "${YELLOW}Note:${NC}"
    echo "  - The .env file must be in the same directory as the executable"
    echo "  - Make sure the backend server is running before launching the app"
    echo "  - You can distribute the entire 'dist' folder"
    echo ""
    echo -e "${GREEN}To run the application:${NC}"
    if [ "$(uname)" == "Darwin" ]; then
        echo "  open dist/CustomSteamDashboard.app"
    else
        echo "  ./dist/CustomSteamDashboard"
    fi
else
    echo -e "${RED}Error: dist directory not found!${NC}"
    exit 1
fi

echo ""
echo "=========================================="

# Create desktop entry file for Linux
if [ "$(uname)" = "Linux" ]; then
    echo -e "${YELLOW}[5/5] Creating desktop entry...${NC}"

    ICONS=$(pwd)/app/icons
    INSTALL_DIR=$(pwd)/dist
    DESKTOP_FILE="$INSTALL_DIR/CustomSteamDashboard.desktop"

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Custom Steam Dashboard
Comment=Custom Steam Dashboard Application
Exec=$INSTALL_DIR/CustomSteamDashboard
Icon=$ICONS/icon-256x256.png
Terminal=false
Categories=Game;Utility;
StartupWMClass=SteamDashboard
EOF

    chmod +x "$DESKTOP_FILE"
    echo -e "${GREEN}✓ Desktop entry created: $DESKTOP_FILE${NC}"
    echo ""
    echo -e "${YELLOW}To install system-wide:${NC}"
    echo "  mkdir -p ~/.local/share/applications"
    echo "  cp $DESKTOP_FILE ~/.local/share/applications/"
    echo "  update-desktop-database ~/.local/share/applications/"
    echo ""
fi
