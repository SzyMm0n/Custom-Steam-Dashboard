#!/bin/bash
# Build script for Custom Steam Dashboard Desktop Application
# Creates a standalone executable using PyInstaller

set -e  # Exit on error

echo "============================================"
echo "Custom Steam Dashboard - Build Executable"
echo "============================================"
echo ""

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading configuration from .env file..."
    export $(grep -v '^#' .env | grep -E '^(SERVER_URL|CLIENT_ID|CLIENT_SECRET)=' | xargs)
    echo "✓ Configuration loaded"
else
    echo "⚠ Warning: .env file not found!"
    echo "  Build will use default values (localhost)"
    echo "  For production build, create .env with:"
    echo "    SERVER_URL=https://your-server.com"
    echo "    CLIENT_ID=your-client-id"
    echo "    CLIENT_SECRET=your-secret"
    echo ""
fi

# Display configuration (hide secret)
echo ""
echo "Build configuration:"
echo "  SERVER_URL: ${SERVER_URL:-http://localhost:8000}"
echo "  CLIENT_ID: ${CLIENT_ID:-desktop-main}"
echo "  CLIENT_SECRET: ${CLIENT_SECRET:+***hidden***}"
if [ -z "$CLIENT_SECRET" ]; then
    echo "  CLIENT_SECRET: ⚠ NOT SET"
fi
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
echo -e "${YELLOW}[2/5] Checking dependencies...${NC}"
python3 -c "import PyInstaller" 2>/dev/null || {
    echo -e "${RED}PyInstaller not found. Installing...${NC}"
    pip install pyinstaller>=6.9
}
echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Generate config.py with embedded values
echo -e "${YELLOW}[3/5] Generating config.py with embedded values...${NC}"
python3 generate_config.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to generate config.py${NC}"
    exit 1
fi
echo ""

# Build executable
echo -e "${YELLOW}[4/5] Building executable...${NC}"
echo "This may take a few minutes..."
echo ""
pyinstaller --clean steam_dashboard.spec
BUILD_RESULT=$?

# Restore original config.py
echo ""
echo -e "${YELLOW}[5/5] Restoring original config.py...${NC}"
python3 restore_config.py
echo ""

if [ $BUILD_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi
echo ""

# Display results
echo "Build complete!"
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
    echo -e "${GREEN}✓ Executable is standalone and ready to distribute!${NC}"
    echo ""
    echo -e "${YELLOW}Configuration embedded in executable:${NC}"
    echo "  ✓ SERVER_URL: ${SERVER_URL:-http://localhost:8000}"
    echo "  ✓ CLIENT_ID: ${CLIENT_ID:-desktop-main}"
    echo "  ✓ CLIENT_SECRET: embedded (hidden for security)"
    echo ""
    echo -e "${YELLOW}Distribution:${NC}"
    echo "  ✓ No .env file needed - configuration is embedded!"
    echo "  ✓ Distribute only the executable file"
    echo "  ✓ Users can run it immediately - zero configuration"
    echo ""
    echo -e "${GREEN}To test the executable:${NC}"
    if [ "$(uname)" == "Darwin" ]; then
        echo "  open dist/CustomSteamDashboard.app"
    else
        echo "  ./dist/CustomSteamDashboard"
    fi
    echo ""
    echo -e "${YELLOW}Optional: Override configuration${NC}"
    echo "  Users can override embedded values with environment variables:"
    echo "  export SERVER_URL=\"http://custom-server.com\""
    echo "  ./CustomSteamDashboard"
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
