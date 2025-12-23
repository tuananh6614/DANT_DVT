"""
Main App - Hệ thống quản lý bãi xe
"""

import sys
import os
import logging
import subprocess
import atexit
from datetime import datetime

# Ensure correct path
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from PySide6.QtWidgets import QApplication, QMainWindow, QInputDialog, QMessageBox
from PySide6.QtCore import Slot, QTimer

# ==================== MQTT BROKER ====================
MOSQUITTO_PATH = r"C:\Program Files\mosquitto\mosquitto.exe"
MOSQUITTO_CONFIG = os.path.join(BASE_DIR, "mosquitto_local.conf")
mosquitto_process = None

def start_mosquitto():
    """Khởi động Mosquitto broker"""
    global mosquitto_process
    
    if not os.path.exists(MOSQUITTO_PATH):
        logging.warning(f"Mosquitto không tìm thấy tại {MOSQUITTO_PATH}")
        return False
    
    # Dừng mosquitto service nếu đang chạy
    try:
        subprocess.run(["taskkill", "/F", "/IM", "mosquitto.exe"], 
                      capture_output=True, timeout=5)
    except:
        pass
    
    # Khởi động mosquitto với config cho phép LAN
    try:
        mosquitto_process = subprocess.Popen(
            [MOSQUITTO_PATH, "-c", MOSQUITTO_CONFIG],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"Mosquitto đã khởi động (PID: {mosquitto_process.pid})")
        return True
    except Exception as e:
        logging.error(f"Không thể khởi động Mosquitto: {e}")
        return False

def stop_mosquitto():
    """Dừng Mosquitto broker"""
    global mosquitto_process
    if mosquitto_process:
        try:
            mosquitto_process.terminate()
            mosquitto_process.wait(timeout=5)
            logging.info("Mosquitto đã dừng")
        except:
            mosquitto_process.kill()
        mosquitto_process = None

from src.database import init_database
from src.mqtt_client import MQTTClient
from src.parking_service import ParkingService
from src.mdns_service import get_mdns_service
from ui.dashboard_widget import DashboardWidget
from ui.card_manager import CardManagerDialog
from ui.qr_payment_widget import QRPaymentWidget
from payment.sepay_helper import create_payment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# mDNS Service
mdns_service = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống quản lý bãi xe")
        self.setMinimumSize(900, 600)
        
        # Components
        self.mqtt_client = MQTTClient(self)
        self.parking_service = ParkingService(self)
        self.dashboard = DashboardWidget()
        self.qr_widget = None
        self.pending_exit = None
        self.card_register_mode = False  # Chế độ đăng ký thẻ
        
        # ESP32 heartbeat timeout (15 giây không nhận được = offline)
        self.esp32_timeout = QTimer(self)
        self.esp32_timeout.timeout.connect(self._on_esp32_timeout)
        self.esp32_timeout.setInterval(15000)  # 15 giây
        
        self.setCentralWidget(self.dashboard)
        
        self._connect_signals()
        self._init_data()
        self.mqtt_client.connect()
    
    def _connect_signals(self):
        # MQTT
        self.mqtt_client.connected.connect(lambda: self.dashboard.set_mqtt_connected(True))
        self.mqtt_client.disconnected.connect(lambda: self.dashboard.set_mqtt_connected(False))
        self.mqtt_client.entry_card_detected.connect(self._on_entry_card)
        self.mqtt_client.exit_card_detected.connect(self._on_exit_card)
        self.mqtt_client.esp32_heartbeat.connect(self._on_esp32_heartbeat)
        self.mqtt_client.slot_status_updated.connect(self._on_slot_status)
        self.mqtt_client.slot_changed.connect(self._on_slot_change)
        
        # Parking
        self.parking_service.entry_success.connect(self._on_entry_success)
        self.parking_service.entry_failed.connect(self._on_entry_failed)
        self.parking_service.exit_ready.connect(self._on_exit_ready)
        self.parking_service.exit_success.connect(self._on_exit_success)
        self.parking_service.exit_failed.connect(self._on_exit_failed)
        # Không dùng slot_updated từ database nữa - lấy từ cảm biến ESP32
        
        # Buttons
        self.dashboard.btn_payment.clicked.connect(self._show_payment_dialog)
        self.dashboard.btn_cards.clicked.connect(self._show_card_manager)
        self.dashboard.btn_manual_entry.clicked.connect(self._manual_entry)
        self.dashboard.btn_manual_exit.clicked.connect(self._manual_exit)
        self.dashboard.btn_reset.clicked.connect(self._reset_database)
    
    def _init_data(self):
        init_database()
        # Chỉ load doanh thu và lịch sử - slot stats lấy từ cảm biến ESP32
        self.dashboard.update_revenue(self.parking_service.get_today_revenue())
        self.dashboard.load_history(self.parking_service.get_recent_history(20))
    
    @Slot(str)
    def _on_entry_card(self, card_id: str):
        # Bỏ qua nếu đang ở chế độ đăng ký thẻ
        if self.card_register_mode:
            return
        success, msg = self.parking_service.process_entry(card_id)
        if success:
            self.mqtt_client.open_entry_barrier()
    
    @Slot(str)
    def _on_exit_card(self, card_id: str):
        # Bỏ qua nếu đang ở chế độ đăng ký thẻ
        if self.card_register_mode:
            return
        self.parking_service.process_exit(card_id)
    
    @Slot(dict)
    def _on_esp32_heartbeat(self, data: dict):
        """Nhận heartbeat từ ESP32"""
        logger.info(f"[HEARTBEAT] Received: {data}")
        data["online"] = True
        self.dashboard.set_esp32_status(data)
        # Reset timeout timer
        self.esp32_timeout.start()
    
    def _on_esp32_timeout(self):
        """ESP32 không gửi heartbeat trong 15 giây"""
        logger.warning("[HEARTBEAT] Timeout - ESP32 offline")
        self.dashboard.set_esp32_offline()
        self.esp32_timeout.stop()
    
    @Slot(dict)
    def _on_slot_status(self, data: dict):
        """Nhận trạng thái tất cả slot từ ESP32"""
        logger.info(f"[SLOT STATUS] {data}")
        self.dashboard.update_all_slots(data)
    
    @Slot(int, bool)
    def _on_slot_change(self, slot: int, occupied: bool):
        """Nhận thông báo slot thay đổi từ ESP32"""
        logger.info(f"[SLOT CHANGE] Slot {slot}: {'Occupied' if occupied else 'Available'}")
        self.dashboard.update_slot(slot, occupied)
    
    @Slot(dict)
    def _on_entry_success(self, data: dict):
        card_id = data.get("card_id", "N/A")
        plate = data.get("plate_number", "N/A")
        slot = data.get("slot_number", 0)
        self.dashboard.add_history_entry(datetime.now().strftime("%H:%M:%S"), "VÀO", card_id, plate, str(slot), "-")
        
        # Gửi thông báo hiển thị lên LCD
        self.mqtt_client.send_lcd_entry(card_id, slot)
    
    @Slot(str)
    def _on_entry_failed(self, msg: str):
        logger.warning(f"[ENTRY FAILED] {msg}")
        QMessageBox.warning(self, "Lỗi vào bãi", msg)
        
        # Gửi thông báo lỗi lên LCD
        self.mqtt_client.send_lcd_error(msg[:20])  # Giới hạn 20 ký tự cho LCD
    
    @Slot(str)
    def _on_exit_failed(self, msg: str):
        logger.warning(f"[EXIT FAILED] {msg}")
        QMessageBox.warning(self, "Lỗi ra bãi", msg)
        
        # Gửi thông báo lỗi lên LCD
        self.mqtt_client.send_lcd_error(msg[:20])
    
    @Slot(dict)
    def _on_exit_ready(self, data: dict):
        session = data["session"]
        fee_info = data["fee_info"]
        
        self.pending_exit = {
            "session_id": session["id"],
            "card_id": session["card_id"],
            "plate_number": session["plate_number"],
            "fee": fee_info["fee"]
        }
        
        # Hiển thị dialog chọn phương thức thanh toán
        self._show_payment_choice_dialog(fee_info["fee"], session["plate_number"])
    
    def _show_payment_choice_dialog(self, fee: int, plate_number: str):
        """Hiển thị dialog chọn thanh toán tiền mặt hoặc online"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Thanh toán")
        dialog.setFixedSize(400, 280)
        dialog.setStyleSheet("QDialog{background:#1a1a2e;}")
        
        # Header
        lbl_title = QLabel("XE RA - THANH TOÁN")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color:#4ade80;font-size:18px;font-weight:bold;margin-bottom:10px;")
        
        # Thông tin
        lbl_plate = QLabel(f"Biển số: {plate_number if plate_number else 'N/A'}")
        lbl_plate.setStyleSheet("color:white;font-size:14px;")
        
        lbl_fee = QLabel(f"Phí gửi xe: {fee:,} VND")
        lbl_fee.setAlignment(Qt.AlignCenter)
        lbl_fee.setStyleSheet("color:#fbbf24;font-size:22px;font-weight:bold;margin:15px 0;")
        
        # Buttons
        btn_cash = QPushButton("TIEN MAT")
        btn_cash.setFixedHeight(50)
        btn_cash.setStyleSheet("""
            QPushButton{background:#22c55e;color:white;border:none;border-radius:8px;font-size:16px;font-weight:bold;}
            QPushButton:hover{background:#16a34a;}
        """)
        
        btn_online = QPushButton("CHUYEN KHOAN")
        btn_online.setFixedHeight(50)
        btn_online.setStyleSheet("""
            QPushButton{background:#3b82f6;color:white;border:none;border-radius:8px;font-size:16px;font-weight:bold;}
            QPushButton:hover{background:#2563eb;}
        """)
        
        btn_cancel = QPushButton("Huy")
        btn_cancel.setFixedHeight(35)
        btn_cancel.setStyleSheet("""
            QPushButton{background:#6b7280;color:white;border:none;border-radius:6px;font-size:13px;}
            QPushButton:hover{background:#4b5563;}
        """)
        
        def pay_cash():
            dialog.close()
            self._complete_exit_cash(fee)
        
        def pay_online():
            dialog.close()
            self._show_payment(fee, plate_number)
        
        def cancel():
            dialog.close()
            self.pending_exit = None
        
        btn_cash.clicked.connect(pay_cash)
        btn_online.clicked.connect(pay_online)
        btn_cancel.clicked.connect(cancel)
        
        # Layout buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addWidget(btn_cash)
        btn_layout.addWidget(btn_online)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(10)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_plate)
        layout.addWidget(lbl_fee)
        layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addWidget(btn_cancel)
        
        dialog.exec()
    
    def _complete_exit_cash(self, fee: int):
        """Hoàn tất xe ra với thanh toán tiền mặt"""
        if self.pending_exit:
            card_id = self.pending_exit.get("card_id", "N/A")
            plate = self.pending_exit.get("plate_number", "N/A")
            self.parking_service.complete_exit(self.pending_exit["session_id"], fee)
            self.mqtt_client.open_exit_barrier()
            
            # Gửi thông báo hiển thị lên LCD
            self.mqtt_client.send_lcd_exit(card_id, fee)
            
            # Thêm vào history
            self.dashboard.add_history_entry(
                datetime.now().strftime("%H:%M:%S"), "RA",
                card_id, plate, "-", f"{fee:,} (TM)"
            )
            self.dashboard.update_revenue(self.parking_service.get_today_revenue())
            logger.info(f"[EXIT CASH] Card {card_id} paid {fee} VND cash")
            self.pending_exit = None
    
    def _complete_exit_free(self):
        if self.pending_exit:
            card_id = self.pending_exit.get("card_id", "N/A")
            plate = self.pending_exit.get("plate_number", "N/A")
            self.parking_service.complete_exit(self.pending_exit["session_id"], 0)
            self.mqtt_client.open_exit_barrier()
            
            # Thêm vào history
            self.dashboard.add_history_entry(
                datetime.now().strftime("%H:%M:%S"), "RA",
                card_id, plate, "-", "Miễn phí"
            )
            logger.info(f"[EXIT FREE] Card {card_id} exited for free")
            self.pending_exit = None
    
    def _show_payment(self, fee: int, plate_number: str):
        order_id = f"P{datetime.now().strftime('%H%M%S')}"
        payment_data = create_payment(fee, order_id)
        
        if not payment_data.get("success"):
            QMessageBox.critical(self, "Lỗi", "Không thể tạo QR thanh toán")
            return
        
        payment_data["plate_number"] = plate_number
        
        if not self.qr_widget:
            self.qr_widget = QRPaymentWidget(self)
            self.qr_widget.payment_success.connect(self._on_payment_success)
            self.qr_widget.payment_cancelled.connect(self._on_payment_cancelled)
        
        self.qr_widget.display_payment(payment_data)
    
    @Slot(dict)
    def _on_payment_success(self, tx_info):
        if self.pending_exit:
            fee = self.pending_exit["fee"]
            card_id = self.pending_exit.get("card_id", "N/A")
            plate = self.pending_exit.get("plate_number", "N/A")
            self.parking_service.complete_exit(self.pending_exit["session_id"], fee)
            self.mqtt_client.open_exit_barrier()
            
            # Gửi thông báo hiển thị lên LCD
            self.mqtt_client.send_lcd_exit(card_id, fee)
            
            self.dashboard.add_history_entry(
                datetime.now().strftime("%H:%M:%S"), "RA",
                card_id, plate, "-", f"{fee:,} (CK)"
            )
            self.dashboard.update_revenue(self.parking_service.get_today_revenue())
            logger.info(f"[EXIT ONLINE] Card {card_id} paid {fee} VND online")
            self.pending_exit = None
    
    @Slot()
    def _on_payment_cancelled(self):
        self.pending_exit = None
    
    @Slot(dict)
    def _on_exit_success(self, data: dict):
        pass
    
    def _show_card_manager(self):
        self.card_register_mode = True
        dialog = CardManagerDialog(self, self.mqtt_client)
        dialog.exec()
        self.card_register_mode = False
    
    def _show_payment_dialog(self):
        """Mở dialog thanh toán online"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Thanh toán Online")
        dialog.setFixedSize(350, 200)
        dialog.setStyleSheet("QDialog{background:#1a1a2e;}")
        
        lbl_amount = QLabel("Số tiền (VND):")
        lbl_amount.setStyleSheet("color:white;font-size:13px;")
        
        txt_amount = QLineEdit()
        txt_amount.setPlaceholderText("Nhập số tiền...")
        txt_amount.setText("10000")
        txt_amount.setStyleSheet("padding:10px;border-radius:6px;border:1px solid #444;background:#2d2d44;color:white;font-size:14px;")
        
        btn_create = QPushButton("🔲 Tạo QR Thanh toán")
        btn_create.setFixedHeight(45)
        btn_create.setStyleSheet("""
            QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2);color:white;border:none;border-radius:8px;font-size:14px;font-weight:bold;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5a6fd6,stop:1 #6a4190);}
        """)
        
        def create_qr():
            try:
                amount = int(txt_amount.text().replace(",", "").strip())
                if amount <= 0:
                    return
                order_id = f"DH{datetime.now().strftime('%H%M%S')}"
                payment_data = create_payment(amount, order_id)
                if payment_data.get("success"):
                    dialog.close()
                    if not self.qr_widget:
                        self.qr_widget = QRPaymentWidget(self)
                        self.qr_widget.payment_success.connect(self._on_payment_success)
                    self.qr_widget.display_payment(payment_data)
            except ValueError:
                pass
        
        btn_create.clicked.connect(create_qr)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(lbl_amount)
        layout.addWidget(txt_amount)
        layout.addStretch()
        layout.addWidget(btn_create)
        
        dialog.exec()
    
    def _manual_entry(self):
        card_id, ok = QInputDialog.getText(self, "Xe vào", "Nhập mã thẻ:")
        if ok and card_id:
            success, msg = self.parking_service.process_entry(card_id.strip())
            if success:
                self.mqtt_client.open_entry_barrier()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)
    
    def _manual_exit(self):
        card_id, ok = QInputDialog.getText(self, "Xe ra", "Nhập mã thẻ:")
        if ok and card_id:
            self.parking_service.process_exit(card_id.strip())
    
    def _reset_database(self):
        """Reset toàn bộ dữ liệu"""
        reply = QMessageBox.question(
            self, "Xác nhận Reset",
            "Bạn có chắc muốn xóa TẤT CẢ dữ liệu?\n\n- Danh sách thẻ\n- Lịch sử vào/ra\n- Doanh thu\n\nHành động này không thể hoàn tác!",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from src import database as db
            from src.config import DATABASE_PATH
            import os
            
            # Xóa file database
            try:
                if os.path.exists(DATABASE_PATH):
                    os.remove(DATABASE_PATH)
                
                # Khởi tạo lại database
                db.init_database()
                
                # Cập nhật UI
                self.dashboard.table_history.setRowCount(0)
                self.dashboard.update_revenue(0)
                
                QMessageBox.information(self, "Thành công", "Đã reset toàn bộ dữ liệu!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể reset: {e}")
    
    def closeEvent(self, event):
        self.mqtt_client.disconnect()
        super().closeEvent(event)


def main():
    global mdns_service
    
    # Khởi động Mosquitto broker
    start_mosquitto()
    atexit.register(stop_mosquitto)
    
    # Chờ Mosquitto khởi động
    import time
    time.sleep(1)
    
    # Khởi động mDNS service để ESP32 tự tìm được broker
    try:
        mdns_service = get_mdns_service()
        if mdns_service.start(mqtt_port=1883):
            local_ip = mdns_service.get_local_ip()
            logger.info(f"[mDNS] MQTT Broker advertised at {local_ip}:1883")
            logger.info(f"[mDNS] ESP32 can connect to: parking-broker.local:1883")
        atexit.register(lambda: mdns_service.stop() if mdns_service else None)
    except Exception as e:
        logger.warning(f"[mDNS] Failed to start: {e}")
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
