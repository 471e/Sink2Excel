@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\release_pipeline.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if "%EXIT_CODE%"=="0" (
    echo Pipeline rilis selesai.
) else (
    echo Pipeline rilis gagal dengan exit code %EXIT_CODE%.
)
echo Log: "%~dp0release_pipeline.log"
pause
exit /b %EXIT_CODE%
