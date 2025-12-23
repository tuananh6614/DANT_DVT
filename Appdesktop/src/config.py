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
}

# Parking Configuration
PARKING_CONFIG = {
    "total_slots": 10,
    "hourly_rate": 5000,      # VND/giờ
    "min_fee": 5000,          # Phí tối thiểu
    "free_minutes": 15,       # Miễn phí 15 phút đầu
}

# Database
DATABASE_PATH = "parking.db"
