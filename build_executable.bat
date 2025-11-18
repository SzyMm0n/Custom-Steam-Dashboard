@echo off
REM Build script for Custom Steam Dashboard Desktop Application
REM Creates a standalone executable using PyInstaller

echo ============================================
echo Custom Steam Dashboard - Build Executable
echo ============================================
echo.

REM Load environment variables from .env file if it exists
if exist .env (
    echo Loading configuration from .env file...
    for /f "usebackq tokens=*" %%a in (.env) do (
        echo %%a | findstr /r "^SERVER_URL=" >nul && set %%a
        echo %%a | findstr /r "^CLIENT_ID=" >nul && set %%a
        echo %%a | findstr /r "^CLIENT_SECRET=" >nul && set %%a
    )
    echo Configuration loaded
) else (
    echo Warning: .env file not found!
    echo   Build will use default values (localhost^)
    echo   For production build, create .env with:
    echo     SERVER_URL=https://your-server.com
    echo     CLIENT_ID=your-client-id
    echo     CLIENT_SECRET=your-secret
    echo.
)

REM Display configuration (hide secret)
echo.
echo Build configuration:
if defined SERVER_URL (
    echo   SERVER_URL: %SERVER_URL%
) else (
    echo   SERVER_URL: http://localhost:8000 (default^)
)
if defined CLIENT_ID (
    echo   CLIENT_ID: %CLIENT_ID%
) else (
    echo   CLIENT_ID: desktop-main (default^)
)
if defined CLIENT_SECRET (
    echo   CLIENT_SECRET: ***hidden***
) else (
    echo   CLIENT_SECRET: NOT SET
)
echo.

REM Check if we're in the correct directory
if not exist "steam_dashboard.spec" (
    echo Error: steam_dashboard.spec not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Clean previous builds
echo [1/5] Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo ✓ Clean complete
echo.

REM Check dependencies
echo [2/5] Checking dependencies...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller>=6.9
)
echo ✓ Dependencies OK
echo.

REM Generate config.py with embedded values
echo [3/5] Generating config.py with embedded values...
python generate_config.py
if errorlevel 1 (
    echo ✗ Failed to generate config.py
    pause
    exit /b 1
)
echo.

REM Build executable
echo [4/5] Building executable...
echo This may take a few minutes...
echo.
pyinstaller --clean steam_dashboard.spec
set BUILD_RESULT=%errorlevel%

REM Restore original config.py
echo.
echo [5/5] Restoring original config.py...
python restore_config.py
echo.

if %BUILD_RESULT% neq 0 (
    echo ✗ Build failed!
    pause
    exit /b 1
)

echo ✓ Build successful!
echo.

REM Display results
echo Build complete!
echo.
echo ==========================================
echo Build Summary
echo ==========================================
echo.

if exist "dist" (
    echo Executable location:
    echo   %CD%\dist\
    echo.

    echo Files created:
    dir /b dist
    echo.
    echo ✓ Executable is standalone and ready to distribute!
    echo.
    echo Configuration embedded in executable:
    if defined SERVER_URL (
        echo   ✓ SERVER_URL: %SERVER_URL%
    ) else (
        echo   ✓ SERVER_URL: http://localhost:8000 (default^)
    )
    if defined CLIENT_ID (
        echo   ✓ CLIENT_ID: %CLIENT_ID%
    ) else (
        echo   ✓ CLIENT_ID: desktop-main (default^)
    )
    echo   ✓ CLIENT_SECRET: embedded (hidden for security^)
    echo.
    echo Distribution:
    echo   ✓ No .env file needed - configuration is embedded!
    echo   ✓ Distribute only the .exe file
    echo   ✓ Users can run it immediately - zero configuration
    echo.
    echo To test the executable:
    echo   dist\CustomSteamDashboard.exe
    echo.
    echo Optional: Override configuration
    echo   Users can override embedded values with environment variables:
    echo   set SERVER_URL=http://custom-server.com
    echo   CustomSteamDashboard.exe
) else (
    echo Error: dist directory not found!
    pause
    exit /b 1
)

echo.
echo ==========================================
pause

