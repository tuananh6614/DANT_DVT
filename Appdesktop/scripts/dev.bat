@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════╗
echo ║   DEV MODE - Auto Reload               ║
echo ╚════════════════════════════════════════╝
echo.

cd /d "%~dp0.."

:: Kiểm tra watchdog
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo [INFO] Đang cài đặt watchdog...
    pip install watchdog
)

echo [INFO] Đang chạy App với Hot Reload...
echo [INFO] Nhấn Ctrl+C để dừng
echo.

python dev_runner.py
