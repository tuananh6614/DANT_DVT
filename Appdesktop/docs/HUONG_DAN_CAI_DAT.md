# 🅿️ Hướng Dẫn Cài Đặt - Hệ Thống Quản Lý Bãi Xe

## 📋 Yêu Cầu Hệ Thống

- Windows 10/11 (64-bit)
- Python 3.10+ (https://python.org) - tick "Add Python to PATH" khi cài
- MQTT Broker (Mosquitto) đang chạy
- Kết nối Internet (cho thanh toán SePay)

---

## 🚀 Cài Đặt Nhanh

```batch
git clone <repo_url>
cd Appdesktop
scripts\install.bat
```

Sau đó:
- **Chạy app:** `scripts\start.bat`
- **Build .exe:** `scripts\build.bat`
- **Xem database:** `scripts\view_db.bat`

---

## 📁 Các File Scripts

| File | Chức năng |
|------|-----------|
| `scripts\install.bat` | Cài đặt tất cả thư viện |
| `scripts\start.bat` | Chạy ứng dụng |
| `scripts\build.bat` | Build thành file .exe |
| `scripts\view_db.bat` | Xem dữ liệu database |

---

## 🔌 Cài Đặt MQTT Broker (Mosquitto)

1. Tải Mosquitto: https://mosquitto.org/download/
2. Cài đặt và chạy service
3. Mặc định chạy trên `localhost:1883`

Kiểm tra:
```batch
netstat -an | findstr 1883
```

---

## ⚙️ Cấu Hình

### File `src/config.py`:

```python
MQTT_CONFIG = {
    "broker": "localhost",      # IP của MQTT broker
    "port": 1883,
    "username": "",             # Nếu có authentication
    "password": "",
}

PARKING_CONFIG = {
    "total_slots": 10,          # Tổng số chỗ
    "hourly_rate": 5000,        # Giá/giờ (VND)
    "free_minutes": 15,         # Miễn phí 15 phút đầu
}
```

### File `payment/sepay_config.py`:
```python
SEPAY_CONFIG = {
    "api_key": "YOUR_API_KEY",
    "bank_code": "VIETINBANK",
    "account_number": "YOUR_ACCOUNT",
    "account_name": "YOUR_NAME",
}
```

---

## 📡 Kết Nối ESP32

### Topics MQTT:

| Topic | Hướng | Mô tả |
|-------|-------|-------|
| `parking/entry/card` | ESP32 → App | Thẻ quét vào |
| `parking/exit/card` | ESP32 → App | Thẻ quét ra |
| `parking/entry/open` | App → ESP32 | Mở barrier vào |
| `parking/exit/open` | App → ESP32 | Mở barrier ra |

### Format message:
```json
{"card_id": "ABC123"}
{"action": "open"}
```

---

## ❓ Xử Lý Lỗi

### MQTT không kết nối (🔴):
- Kiểm tra Mosquitto đang chạy
- Kiểm tra IP/port trong config.py
- Kiểm tra firewall

### Thanh toán không hoạt động:
- Kiểm tra API key SePay
- Kiểm tra kết nối Internet
- Nội dung chuyển khoản phải có prefix "SEVQR"

### App không mở:
- Cài đặt Visual C++ Redistributable
- Chạy với quyền Administrator
