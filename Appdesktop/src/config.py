"""
Configuration - MQTT, Database, Pricing
"""

# MQTT Configuration
MQTT_CONFIG = {
    "broker": "localhost",
    "port": 1883,
    "username": "",
    "password": "",
    "client_id": "parking_desktop",
    "keepalive": 60,
}

# MQTT Topics
MQTT_TOPICS = {
    "entry_card": "parking/entry/card",      # ESP32 -> App: thẻ quét vào
    "exit_card": "parking/exit/card",        # ESP32 -> App: thẻ quét ra
    "entry_open": "parking/entry/open",      # App -> ESP32: mở barrier vào
    "exit_open": "parking/exit/open",        # App -> ESP32: mở barrier ra
    "status": "parking/status",              # App -> ESP32: trạng thái
    "esp32_heartbeat": "parking/esp32/heartbeat",  # ESP32 -> App: heartbeat
    "slot_status": "parking/slots/status",   # ESP32 -> App: trạng thái tất cả slot
    "slot_change": "parking/slots/change",   # ESP32 -> App: slot thay đổi
    "lcd_entry": "parking/lcd/entry",        # App -> ESP32: hiển thị xe vào
    "lcd_exit": "parking/lcd/exit",          # App -> ESP32: hiển thị xe ra
    "lcd_error": "parking/lcd/error",        # App -> ESP32: hiển thị lỗi
}

# Parking Configuration
PARKING_CONFIG = {
    "total_slots": 10,
    "hourly_rate": 5000,      # VND/giờ
    "min_fee": 5000,          # Phí tối thiểu
    "free_minutes": 15,       # Miễn phí 15 phút đầu
}

# Database
import os
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(_BASE_DIR, "parking.db")
