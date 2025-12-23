# 🅿️ THÔNG TIN PHẦN MỀM QUẢN LÝ BÃI XE

## 📌 Tổng Quan

| Thông tin | Chi tiết |
|-----------|----------|
| **Tên phần mềm** | Hệ Thống Quản Lý Bãi Xe Thông Minh |
| **Phiên bản** | 1.0.0 |
| **Ngôn ngữ** | Python 3.10+ |
| **Framework UI** | PySide6 (Qt6) |
| **Database** | SQLite |
| **Giao tiếp IoT** | MQTT Protocol |
| **Thanh toán** | SePay (VietQR) |

---

## 🎯 Chức Năng Chính

### 1. Quản Lý Xe Vào/Ra
- Quét thẻ RFID tự động qua ESP32
- Nhập thủ công mã thẻ
- Ghi nhận thời gian vào/ra
- Tự động gán slot trống

### 2. Quản Lý Thẻ RFID
- Thêm/Xóa thẻ
- Gán thông tin: Tên chủ xe, Biển số, SĐT
- Danh sách thẻ đang hoạt động

### 3. Tính Phí Tự Động
- Tính theo giờ (mặc định: 5,000 VND/giờ)
- Miễn phí 15 phút đầu
- Phí tối thiểu có thể cấu hình

### 4. Thanh Toán Online (SePay)
- Tạo mã QR VietQR tự động
- Xác thực thanh toán real-time (polling API)
- Hiệu ứng animation khi thanh toán thành công
- Hỗ trợ tất cả ngân hàng Việt Nam

### 5. Dashboard Thống Kê
- Số chỗ trống / Tổng slot
- Số xe đang trong bãi
- Doanh thu hôm nay
- Lịch sử vào/ra gần nhất

### 6. Kết Nối ESP32
- Giao tiếp qua MQTT
- Điều khiển barrier vào/ra
- Nhận tín hiệu quét thẻ RFID
- Auto-reconnect khi mất kết nối

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────┐     MQTT      ┌─────────────┐
│   ESP32     │◄────────────►│  Desktop    │
│  + RFID     │               │    App      │
│  + Barrier  │               │  (Python)   │
└─────────────┘               └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │   SQLite    │
                              │  Database   │
                              └─────────────┘
                                     │
                              ┌──────▼──────┐
                              │   SePay     │
                              │    API      │
                              └─────────────┘
```

---

## 📂 Cấu Trúc Thư Mục

```
Appdesktop/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .gitignore
│
├── src/                    # Business Logic
│   ├── config.py           # Cấu hình MQTT, giá tiền
│   ├── database.py         # SQLite operations
│   ├── mqtt_client.py      # Kết nối ESP32
│   ├── parking_service.py  # Xử lý vào/ra
│   ├── fee_calculator.py   # Tính phí
│   └── models.py           # Data models
│
├── ui/                     # Giao Diện
│   ├── dashboard_widget.py # Màn hình chính
│   ├── card_manager.py     # Quản lý thẻ
│   ├── qr_payment_widget.py# Thanh toán QR
│   └── success_dialog.py   # Animation thành công
│
├── payment/                # Thanh Toán
│   ├── sepay_config.py     # Cấu hình SePay
│   └── sepay_helper.py     # Tạo QR, verify
│
├── scripts/                # Scripts
│   ├── install.bat         # Cài đặt
│   ├── start.bat           # Chạy app
│   ├── build.bat           # Build .exe
│   └── view_db.bat         # Xem database
│
└── docs/                   # Tài Liệu
    ├── README.md
    ├── HUONG_DAN_CAI_DAT.md
    └── THONG_TIN_PHAN_MEM.md
```

---

## 🗄️ Cơ Sở Dữ Liệu

### Bảng `cards` - Thẻ RFID
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| id | INTEGER | Primary key |
| card_id | TEXT | Mã thẻ RFID (unique) |
| owner_name | TEXT | Tên chủ xe |
| plate_number | TEXT | Biển số xe |
| phone | TEXT | Số điện thoại |
| is_active | INTEGER | Trạng thái (1=active) |

### Bảng `sessions` - Phiên Gửi Xe
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| id | INTEGER | Primary key |
| card_id | TEXT | Mã thẻ |
| plate_number | TEXT | Biển số |
| slot_number | INTEGER | Số slot |
| entry_time | TIMESTAMP | Thời gian vào |
| exit_time | TIMESTAMP | Thời gian ra |
| fee | INTEGER | Phí (VND) |
| payment_status | TEXT | pending/paid |

### Bảng `slots` - Chỗ Đỗ Xe
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| slot_number | INTEGER | Số slot (1-10) |
| is_occupied | INTEGER | 0=trống, 1=có xe |
| current_session_id | INTEGER | Session đang dùng |

---

## 📡 MQTT Topics

| Topic | Hướng | Payload | Mô tả |
|-------|-------|---------|-------|
| `parking/entry/card` | ESP32 → App | `{"card_id": "ABC123"}` | Thẻ quét vào |
| `parking/exit/card` | ESP32 → App | `{"card_id": "ABC123"}` | Thẻ quét ra |
| `parking/entry/open` | App → ESP32 | `{"action": "open"}` | Mở barrier vào |
| `parking/exit/open` | App → ESP32 | `{"action": "open"}` | Mở barrier ra |
| `parking/status` | App → ESP32 | `{"slots_available": 5}` | Trạng thái bãi |

---

## 💳 Tích Hợp SePay

### Luồng Thanh Toán:
1. App tạo mã QR với số tiền + nội dung
2. Khách quét QR bằng app ngân hàng
3. App polling API SePay mỗi 3 giây
4. Khi phát hiện giao dịch khớp → Xác nhận thành công
5. Mở barrier cho xe ra

### Cấu Hình:
- **API Key**: Lấy từ my.sepay.vn
- **Bank Code**: VIETINBANK, VIETCOMBANK, ...
- **Content Prefix**: SEVQR (bắt buộc cho VietinBank)

---

## ⚙️ Cấu Hình Mặc Định

```python
# MQTT
broker = "localhost"
port = 1883

# Bãi xe
total_slots = 10
hourly_rate = 5000      # VND/giờ
free_minutes = 15       # Miễn phí 15 phút đầu
min_fee = 5000          # Phí tối thiểu
```

---

## 🔧 Công Nghệ Sử Dụng

| Thành phần | Công nghệ |
|------------|-----------|
| UI Framework | PySide6 (Qt6) |
| Database | SQLite3 |
| MQTT Client | paho-mqtt 2.x |
| HTTP Client | requests |
| Build Tool | PyInstaller |
| IoT Device | ESP32 + RC522 RFID |

---

## 📞 Liên Hệ & Hỗ Trợ

- **Developer**: [Tên của bạn]
- **Email**: [Email của bạn]
- **Phone**: [SĐT của bạn]

---

*Phiên bản: 1.0.0 | Cập nhật: Tháng 12/2024*
