# 🅿️ Hệ Thống Quản Lý Bãi Xe

Desktop app quản lý bãi xe với ESP32 + MQTT + Thanh toán SePay.

## 🚀 Cài đặt & Chạy

```batch
# 1. Cài đặt
scripts\install.bat

# 2. Chạy app
scripts\start.bat

# 3. Build .exe (optional)
scripts\build.bat
```

## ⚙️ Cấu hình

| File | Mô tả |
|------|-------|
| `src/config.py` | MQTT broker, giá tiền, số slot |
| `payment/sepay_config.py` | API key SePay, thông tin ngân hàng |

## 📁 Cấu trúc

```
Appdesktop/
├── main.py              # Entry point
├── src/                 # Business logic
├── ui/                  # Giao diện
├── payment/             # Thanh toán SePay
├── scripts/             # Các file .bat
│   ├── install.bat
│   ├── start.bat
│   ├── build.bat
│   └── view_db.bat
└── docs/                # Tài liệu
    ├── README.md
    └── HUONG_DAN_CAI_DAT.md
```

## 📋 Yêu cầu

- Python 3.10+
- MQTT Broker (Mosquitto)
- Internet (cho thanh toán)

📖 Chi tiết: [HUONG_DAN_CAI_DAT.md](HUONG_DAN_CAI_DAT.md)
