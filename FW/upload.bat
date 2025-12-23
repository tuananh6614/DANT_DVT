@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════╗
echo ║   NẠP CODE ESP32 - BÃI XE THÔNG MINH  ║
echo ╚════════════════════════════════════════╝
echo.

:: Kiểm tra PlatformIO
where pio >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PlatformIO chưa được cài đặt!
    echo.
    echo Cài đặt: pip install platformio
    echo Hoặc cài VS Code + PlatformIO Extension
    echo.
    pause
    exit /b 1
)

echo [1/2] Đang biên dịch...
pio run

if errorlevel 1 (
    echo.
    echo [ERROR] Biên dịch thất bại!
    pause
    exit /b 1
)

echo.
echo [2/2] Đang nạp code vào ESP32...
echo      (Nhấn nút BOOT trên ESP32 nếu cần)
echo.
pio run -t upload

if errorlevel 1 (
    echo.
    echo [ERROR] Nạp code thất bại!
    echo Kiểm tra:
    echo   - ESP32 đã cắm USB chưa?
    echo   - Driver CH340/CP2102 đã cài chưa?
    echo   - Nhấn giữ nút BOOT khi nạp
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════
echo   ✅ NẠP CODE THÀNH CÔNG!
echo.
echo   Mở Serial Monitor: pio device monitor
echo   Hoặc nhấn phím bất kỳ để mở...
echo ════════════════════════════════════════
echo.
pause

pio device monitor
