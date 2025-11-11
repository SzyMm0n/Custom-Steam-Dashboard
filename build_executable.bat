@echo off
REM Build script for Custom Steam Dashboard executable (Windows)
REM This script creates a standalone executable for the desktop application

echo ==========================================
echo Custom Steam Dashboard - Build Executable
echo ==========================================
echo.

REM Check if we're in the correct directory
if not exist "steam_dashboard.spec" (
    echo Error: steam_dashboard.spec not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Clean previous builds
echo [1/4] Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo ✓ Clean complete
echo.

REM Check dependencies
echo [2/4] Checking dependencies...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller>=6.9
)
echo ✓ Dependencies OK
echo.

REM Build executable
echo [3/4] Building executable...
echo This may take a few minutes...
echo.
pyinstaller --clean steam_dashboard.spec

if errorlevel 1 (
    echo.
    echo ✗ Build failed!
    pause
    exit /b 1
)

echo.
echo ✓ Build successful!
echo.

REM Display results
echo [4/4] Build complete!
echo.
echo ==========================================
echo Build Summary
echo ==========================================
echo.

if exist "dist" (
    echo Executable location:
    echo   %CD%\dist\
    echo.

    REM Copy .env.example as .env to dist folder if it doesn't exist
    if not exist "dist\.env" (
        if exist ".env.example" (
            copy .env.example dist\.env >nul
            echo ✓ Created dist\.env from .env.example
            echo ⚠ IMPORTANT: Edit dist\.env with your credentials!
            echo.
        )
    )

    REM Copy README_USER.md to dist folder
    if exist "README_USER.md" (
        copy README_USER.md dist\ >nul
        echo ✓ Copied README_USER.md to dist\
        echo.
    )

    echo Files created:
    dir /b dist
    echo.
    echo Configuration:
    echo   1. Edit dist\.env file with your settings:
    echo      - SERVER_URL ^(backend API URL^)
    echo      - CLIENT_ID and CLIENT_SECRET ^(authentication^)
    echo   2. Make sure these match your server configuration
    echo.
    echo Note:
    echo   - The .env file must be in the same directory as the executable
    echo   - Make sure the backend server is running before launching the app
    echo   - You can distribute the entire 'dist' folder
    echo.
    echo To run the application:
    echo   dist\CustomSteamDashboard.exe
) else (
    echo Error: dist directory not found!
    pause
    exit /b 1
)

echo.
echo ==========================================
pause

