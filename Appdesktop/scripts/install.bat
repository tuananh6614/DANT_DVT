@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo.
echo ========================================
echo    CAI DAT HE THONG QUAN LY BAI XE
echo ========================================
echo.

REM ==================== KIEM TRA PYTHON ====================
echo [1/5] Kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python chua duoc cai dat!
    echo.
    echo Tai Python tai: https://python.org
    echo QUAN TRONG: Tick chon "Add Python to PATH" khi cai!
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo         Python %PYVER% - OK

REM ==================== CAI DAT THU VIEN ====================
echo.
echo [2/5] Cai dat thu vien Python...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [ERROR] Cai dat thu vien that bai!
    echo Thu chay: pip install -r requirements.txt
    pause
    exit /b 1
)
echo         Thu vien - OK

REM ==================== KHOI TAO DATABASE ====================
echo.
echo [3/5] Khoi tao database...
python -c "from src.database import init_database; init_database()"
if errorlevel 1 (
    echo [WARNING] Khong the khoi tao database tu dong
) else (
    echo         Database - OK
)

REM ==================== KIEM TRA MOSQUITTO ====================
echo.
echo [4/5] Kiem tra Mosquitto MQTT Broker...
if exist "C:\Program Files\mosquitto\mosquitto.exe" (
    echo         Mosquitto - OK
) else (
    echo [WARNING] Mosquitto chua cai dat!
    echo.
    echo Tai Mosquitto tai: https://mosquitto.org/download/
    echo Chon phien ban Windows 64-bit
    echo.
)

REM ==================== TAO SHORTCUT ====================
echo.
echo [5/5] Tao shortcut...
set SCRIPT_PATH=%~dp0start.bat
set SHORTCUT_PATH=%USERPROFILE%\Desktop\ParkingManager.lnk

REM Tao shortcut bang PowerShell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%SCRIPT_PATH%'; $s.WorkingDirectory = '%~dp0..'; $s.Description = 'He thong Quan ly Bai xe'; $s.Save()" >nul 2>&1
if exist "%SHORTCUT_PATH%" (
    echo         Shortcut tren Desktop - OK
) else (
    echo         Khong tao duoc shortcut
)

REM ==================== HOAN TAT ====================
echo.
echo ========================================
echo    CAI DAT HOAN TAT!
echo ========================================
echo.
echo    Chay app:     scripts\start.bat
echo    Build .exe:   scripts\build.bat
echo.
echo    Hoac click shortcut "ParkingManager"
echo    tren Desktop
echo.
echo ========================================
echo.

REM Hoi nguoi dung co muon chay app ngay khong
set /p RUN_NOW="Ban co muon chay app ngay bay gio? (Y/N): "
if /i "%RUN_NOW%"=="Y" (
    call "%~dp0start.bat"
)

pause
