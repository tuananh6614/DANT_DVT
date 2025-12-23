@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo.
echo ╔════════════════════════════════════════╗
echo ║   BUILD FILE .EXE                      ║
echo ╚════════════════════════════════════════╝
echo.

echo [1/2] Cài đặt PyInstaller...
pip install pyinstaller --quiet

echo [2/2] Đang build .exe (có thể mất 2-3 phút)...
pyinstaller --noconfirm --onedir --windowed ^
    --name "ParkingManager" ^
    --add-data "src;src" ^
    --add-data "ui;ui" ^
    --add-data "payment;payment" ^
    --hidden-import "paho.mqtt.client" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    main.py

echo.
echo ════════════════════════════════════════
echo   ✅ BUILD HOÀN TẤT!
echo.
echo   File .exe tại: dist\ParkingManager\
echo ════════════════════════════════════════
echo.

explorer dist\ParkingManager
pause
