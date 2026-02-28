"%PYTHON%" -m pip install . -vv --no-deps --no-build-isolation
if errorlevel 1 exit 1

rem Install examples and notebooks to share directory
set SHARE_DIR=%PREFIX%\share\pyvis
mkdir "%SHARE_DIR%\examples" 2>nul
mkdir "%SHARE_DIR%\notebooks" 2>nul
copy examples\*.py "%SHARE_DIR%\examples\"
copy notebooks\*.ipynb "%SHARE_DIR%\notebooks\"
copy notebooks\*.csv "%SHARE_DIR%\notebooks\" 2>nul
copy notebooks\*.dot "%SHARE_DIR%\notebooks\" 2>nul
