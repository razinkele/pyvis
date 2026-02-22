@echo off
REM Create dedicated conda environment for PyVis Optimized

echo ============================================================
echo PyVis Optimized - Conda Environment Setup
echo ============================================================
echo.

REM Check if conda is available
conda --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Conda not found! Please install Miniconda or Anaconda.
    echo Download from: https://docs.conda.io/en/latest/miniconda.html
    exit /b 1
)

echo Creating conda environment 'pyvis-optimized'...
echo.

REM Create environment from yml file
conda env create -f environment.yml

if errorlevel 1 (
    echo.
    echo [ERROR] Environment creation failed!
    echo.
    echo Try creating manually:
    echo   conda create -n pyvis-optimized python=3.10
    echo   conda activate pyvis-optimized
    echo   pip install -e .
    exit /b 1
)

echo.
echo ============================================================
echo Environment Created Successfully!
echo ============================================================
echo.
echo To activate the environment:
echo   conda activate pyvis-optimized
echo.
echo Then install PyVis:
echo   pip install -e .
echo.
echo Or with Shiny:
echo   pip install -e ".[shiny]"
echo ============================================================
