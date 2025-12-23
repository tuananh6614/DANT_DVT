@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========================================
echo    DONG GOI HE THONG DE BAN GIAO
echo ========================================
echo.

set DELIVERY_DIR=ParkingSystem_BanGiao
set DELIVERY_PATH=%~dp0%DELIVERY_DIR%

echo [1/6] Tao thu muc ban giao...
if exist "%DELIVERY_PATH%" rmdir /s /q "%DELIVERY_PATH%"
mkdir "%DELIVERY_PATH%"
mkdir "%DELIVERY_PATH%\App"
mkdir "%DELIVERY_PATH%\Firmware"
mkdir "%DELIVERY_PATH%\Mosquitto"

echo [2/6] Copy App Desktop...
xcopy /E /I /Y "Appdesktop\src" "%DELIVERY_PATH%\App\src" >nul
xcopy /E /I /Y "Appdesktop\ui" "%DELIVERY_PATH%\App\ui" >nul
xcopy /E /I /Y "Appdesktop\payment" "%DELIVERY_PATH%\App\payment" >nul
xcopy /E /I /Y "Appdesktop\docs" "%DELIVERY_PATH%\App\docs" >nul
mkdir "%DELIVERY_PATH%\App\scripts"
copy /Y "Appdesktop\scripts\install.bat" "%DELIVERY_PATH%\App\scripts\" >nul
copy /Y "Appdesktop\scripts\start.bat" "%DELIVERY_PATH%\App\scripts\" >nul
copy /Y "Appdesktop\scripts\build.bat" "%DELIVERY_PATH%\App\scripts\" >nul
copy /Y "Appdesktop\main.py" "%DELIVERY_PATH%\App\" >nul
copy /Y "Appdesktop\requirements.txt" "%DELIVERY_PATH%\App\" >nul
copy /Y "Appdesktop\mosquitto_local.conf" "%DELIVERY_PATH%\App\" >nul

echo [3/6] Copy Firmware ESP32...
xcopy /E /I /Y "FW\src" "%DELIVERY_PATH%\Firmware\src" >nul
xcopy /E /I /Y "FW\include" "%DELIVERY_PATH%\Firmware\include" >nul
xcopy /E /I /Y "FW\lib" "%DELIVERY_PATH%\Firmware\lib" >nul
copy /Y "FW\platformio.ini" "%DELIVERY_PATH%\Firmware\" >nul
copy /Y "FW\upload.bat" "%DELIVERY_PATH%\Firmware\" >nul

echo [4/6] Tao cau hinh Mosquitto...
(
echo # Mosquitto Configuration for Parking System
echo # Copy file nay vao: C:\Program Files\mosquitto\
echo.
echo allow_anonymous true
echo listener 1883 0.0.0.0
echo.
echo log_dest file mosquitto.log
echo log_type all
) > "%DELIVERY_PATH%\Mosquitto\mosquitto.conf"

(
echo @echo off
echo echo ========================================
echo echo    CAI DAT MOSQUITTO MQTT BROKER
echo echo ========================================
echo echo.
echo echo 1. Tai Mosquitto tai: https://mosquitto.org/download/
echo echo    Chon phien ban Windows 64-bit
echo echo.
echo echo 2. Cai dat va chon "Install as service"
echo echo.
echo echo 3. Copy file mosquitto.conf vao:
echo echo    C:\Program Files\mosquitto\
echo echo.
echo echo 4. Khoi dong lai Mosquitto:
echo echo    net stop mosquitto
echo echo    net start mosquitto
echo echo.
echo pause
) > "%DELIVERY_PATH%\Mosquitto\HUONG_DAN.bat"

echo [5/6] Tao file README...
(
echo ========================================
echo    HE THONG QUAN LY BAI XE
echo ========================================
echo.
echo THU MUC:
echo - App/       : Ung dung quan ly ^(Python^)
echo - Firmware/  : Code ESP32 ^(PlatformIO^)
echo - Mosquitto/ : Cau hinh MQTT Broker
echo.
echo ========================================
echo    HUONG DAN CAI DAT
echo ========================================
echo.
echo BUOC 1: Cai dat Mosquitto MQTT Broker
echo   - Xem file: Mosquitto\HUONG_DAN.bat
echo.
echo BUOC 2: Cai dat App Desktop
echo   - Cai Python 3.10+ tu https://python.org
echo   - QUAN TRONG: Tick "Add Python to PATH"
echo   - Chay: App\scripts\install.bat
echo.
echo BUOC 3: Nap firmware ESP32
echo   - Cai PlatformIO trong VS Code
echo   - Mo thu muc Firmware
echo   - Nhan Upload
echo.
echo BUOC 4: Cau hinh ESP32
echo   - Ket noi WiFi: ParkingESP32_Setup ^(pass: 12345678^)
echo   - Truy cap: http://192.168.4.1
echo   - Nhap WiFi va de trong MQTT Server ^(tu dong tim^)
echo.
echo ========================================
echo    KHOI DONG HE THONG
echo ========================================
echo.
echo 1. Mosquitto tu dong chay khi bat may
echo 2. Chay App: App\scripts\start.bat
echo 3. Cap nguon ESP32
echo.
echo Xem chi tiet: App\docs\HUONG_DAN_TRIEN_KHAI.md
echo.
) > "%DELIVERY_PATH%\README.txt"

echo [6/6] Hoan tat!
echo.
echo ========================================
echo    DONG GOI HOAN TAT!
echo.
echo    Thu muc: %DELIVERY_DIR%
echo.
echo    Nen thanh file .zip de gui khach
echo ========================================
echo.

explorer "%DELIVERY_PATH%"
pause
