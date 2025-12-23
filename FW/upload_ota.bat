@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════╗
echo ║   NẠP CODE QUA OTA (WiFi)              ║
echo ╚════════════════════════════════════════╝
echo.
echo   IP cố định ESP32: 192.168.1.88
echo.

set IP=192.168.1.88

echo [INFO] Đang nạp code đến %IP%...
echo [INFO] Password: parking123
echo.

pio run -t upload --upload-port %IP%

if errorlevel 1 (
    echo.
    echo [ERROR] Nạp OTA thất bại!
    echo Kiểm tra:
    echo   - ESP32 đã kết nối WiFi chưa?
    echo   - ESP32 và máy tính cùng mạng 192.168.1.x?
    echo   - Router có cho phép IP 192.168.1.88?
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════
echo   ✅ NẠP OTA THÀNH CÔNG!
echo ════════════════════════════════════════
pause
