@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo.
echo ╔════════════════════════════════════════╗
echo ║   CÀI ĐẶT HỆ THỐNG QUẢN LÝ BÃI XE     ║
echo ╚════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python chưa được cài đặt!
    echo Tải Python tại: https://python.org
    echo Nhớ tick "Add Python to PATH" khi cài!
    pause
    exit /b 1
)

echo [1/2] Đang cài đặt thư viện...
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [ERROR] Cài đặt thất bại!
    pause
    exit /b 1
)

echo [2/2] Khởi tạo database...
python -c "from src.database import init_database; init_database()"

echo.
echo ════════════════════════════════════════
echo   ✅ CÀI ĐẶT HOÀN TẤT!
echo.
echo   Chạy app:     scripts\start.bat
echo   Build .exe:   scripts\build.bat
echo ════════════════════════════════════════
pause
