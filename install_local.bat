@echo off
REM Quick installation script for PyVis Optimized in current environment

echo ============================================================
echo PyVis Optimized - Local Installation Script
echo ============================================================
echo.

REM Check Python
python --version
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python or activate conda environment.
    exit /b 1
)

echo.
echo Current environment:
python -c "import sys; print(f'  Python: {sys.executable}')"
python -c "import sys; import os; env = os.environ.get('CONDA_DEFAULT_ENV', 'system'); print(f'  Environment: {env}')"

echo.
echo Choose installation option:
echo   1. Basic installation (core only)
echo   2. With Shiny support
echo   3. Development mode (all tools)
echo   4. Full installation (everything)
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Installing PyVis (basic)...
    pip install -e .
) else if "%choice%"=="2" (
    echo.
    echo Installing PyVis with Shiny support...
    pip install -e ".[shiny]"
) else if "%choice%"=="3" (
    echo.
    echo Installing PyVis in development mode...
    pip install -e ".[dev]"
) else if "%choice%"=="4" (
    echo.
    echo Installing PyVis with all features...
    pip install -e ".[all]"
) else (
    echo Invalid choice!
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed!
    exit /b 1
)

echo.
echo ============================================================
echo Verifying Installation...
echo ============================================================

python -c "import pyvis; print(f'PyVis version: {pyvis.__version__}')"
python -c "from pyvis.network import Network, CDN_REMOTE; print('Core imports: OK')"
python -c "from pyvis.network import VALID_CDN_RESOURCES; print(f'Constants: {VALID_CDN_RESOURCES}')"

echo.
echo ============================================================
echo Installation Successful!
echo ============================================================
echo.
echo Quick test:
echo   python test_new_features.py
echo.
echo Run benchmarks:
echo   python benchmark_improvements.py
echo.
echo Run examples:
echo   shiny run shiny_modern_example.py
echo ============================================================
