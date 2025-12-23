@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo.
echo ╔════════════════════════════════════════╗
echo ║   XEM DỮ LIỆU DATABASE                 ║
echo ╚════════════════════════════════════════╝
echo.

python -c "
import sqlite3
conn = sqlite3.connect('parking.db')
cursor = conn.cursor()

print('=== THẺ RFID ===')
cursor.execute('SELECT card_id, owner_name, plate_number FROM cards WHERE is_active=1')
rows = cursor.fetchall()
if rows:
    for r in rows: print(f'  {r[0]} | {r[1]} | {r[2]}')
else:
    print('  (Chưa có thẻ nào)')

print()
print('=== SLOTS ===')
cursor.execute('SELECT slot_number, is_occupied FROM slots')
for r in cursor.fetchall():
    status = '🚗 Có xe' if r[1] else '✅ Trống'
    print(f'  Slot {r[0]}: {status}')

print()
print('=== 5 PHIÊN GẦN NHẤT ===')
cursor.execute('SELECT plate_number, entry_time, exit_time, fee FROM sessions ORDER BY id DESC LIMIT 5')
rows = cursor.fetchall()
if rows:
    for r in rows:
        status = f'Ra: {r[2][:16]} - {r[3]:,}đ' if r[2] else 'Đang trong bãi'
        print(f'  {r[0]} | Vào: {r[1][:16]} | {status}')
else:
    print('  (Chưa có phiên nào)')

conn.close()
"
echo.
pause
