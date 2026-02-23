@echo off
REM Build script for PyVis Optimized Package
REM Run this to create distributable packages

echo ============================================================
echo PyVis Optimized - Package Build Script
echo ============================================================
echo.

REM Check if build tools are installed
python -c "import build" 2>nul
if errorlevel 1 (
    echo Installing build tools...
    pip install build wheel setuptools
)

echo.
echo Step 1: Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist pyvis.egg-info rmdir /s /q pyvis.egg-info
echo [OK] Cleaned

echo.
echo Step 2: Building package...
python -m build
if errorlevel 1 (
    echo [ERROR] Build failed!
    exit /b 1
)
echo [OK] Built successfully

echo.
echo Step 3: Listing built packages...
dir dist\*.*
echo.

echo ============================================================
echo Build Complete!
echo ============================================================
echo.
echo Created files in dist/:
echo   - pyvis-4.0.0-py3-none-any.whl  (wheel package)
echo   - pyvis-4.0.0.tar.gz            (source distribution)
echo.
echo To install:
echo   pip install dist\pyvis-4.0.0-py3-none-any.whl
echo.
echo Or in development mode:
echo   pip install -e .
echo ============================================================
