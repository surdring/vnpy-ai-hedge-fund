@echo off
chcp 65001 >nul
cd /d d:\develop\vnpy-ai-hedge-fund

REM Clear Trae sandbox env vars
set PYTHONSTARTUP=
set TRAE_SANDBOX_ENABLED=

REM -E ignores all PYTHON* env vars (like PYTHONSTARTUP)
python -E run_veighna_ai.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Launch failed (error code: %ERRORLEVEL%)
)
pause