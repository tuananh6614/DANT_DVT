@echo off
chcp 65001 >nul
echo Đang mở Serial Monitor (115200 baud)...
echo Nhấn Ctrl+C để thoát
echo.
pio device monitor
