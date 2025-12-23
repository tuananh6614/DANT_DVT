"""
Main App - Hệ thống quản lý bãi xe
"""

import sys
import os
import logging
from datetime import datetime

# Ensure correct path
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from PySide6.QtWidgets import QApplication, QMainWindow, QInputDialog, QMessageBox
from PySide6.QtCore import Slot

from src.database import init_database
from src.mqtt_client import MQTTClient
from src.parking_service import ParkingService
from ui.dashboard_widget import DashboardWidget
from ui.card_manager import CardManagerDialog
from ui.qr_payment_widget import QRPaymentWidget
from payment.sepay_helper import create_payment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
        
        # Parking
        self.parking_service.entry_success.connect(self._on_entry_success)
        self.parking_service.entry_failed.connect(self._on_entry_failed)
        self.parking_service.exit_ready.connect(self._on_exit_ready)
        self.parking_service.exit_success.connect(self._on_exit_success)
        self.parking_service.slot_updated.connect(self.dashboard.update_slot_stats)
        
        # Buttons
        self.dashboard.btn_payment.clicked.connect(self._show_payment_dialog)
        self.dashboard.btn_cards.clicked.connect(self._show_card_manager)
        self.dashboard.btn_manual_entry.clicked.connect(self._manual_entry)
        self.dashboard.btn_manual_exit.clicked.connect(self._manual_exit)
    
    def _init_data(self):
        init_database()
        stats = self.parking_service.get_slot_stats()
        self.dashboard.update_slot_stats(stats)
        self.dashboard.update_revenue(self.parking_service.get_today_revenue())
        self.dashboard.load_history(self.parking_service.get_recent_history(20))
    
    @Slot(str)
    def _on_entry_card(self, card_id: str):
        success, msg = self.parking_service.process_entry(card_id)
        if success:
            self.mqtt_client.open_entry_barrier()
    
    @Slot(str)
    def _on_exit_card(self, card_id: str):
        self.parking_service.process_exit(card_id)
    
    @Slot(dict)
    def _on_entry_success(self, data: dict):
        plate = data.get("plate_number", "N/A")
        slot = str(data.get("slot_number", ""))
        self.dashboard.add_history_entry(datetime.now().strftime("%H:%M:%S"), "VÀO", plate, slot, "-")
    
    @Slot(str)
    def _on_entry_failed(self, msg: str):
        QMessageBox.warning(self, "Lỗi vào bãi", msg)
    
    @Slot(dict)
    def _on_exit_ready(self, data: dict):
        session = data["session"]
        fee_info = data["fee_info"]
        
        self.pending_exit = {
            "session_id": session["id"],
            "plate_number": session["plate_number"],
            "fee": fee_info["fee"]
        }
        
        if fee_info["fee"] == 0:
            self._complete_exit_free()
        else:
            self._show_payment(fee_info["fee"], session["plate_number"])
    
    def _complete_exit_free(self):
        if self.pending_exit:
            self.parking_service.complete_exit(self.pending_exit["session_id"], 0)
            self.mqtt_client.open_exit_barrier()
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
            self.parking_service.complete_exit(self.pending_exit["session_id"], fee)
            self.mqtt_client.open_exit_barrier()
            
            self.dashboard.add_history_entry(
                datetime.now().strftime("%H:%M:%S"), "RA",
                self.pending_exit["plate_number"], "-", f"{fee:,}"
            )
            self.dashboard.update_revenue(self.parking_service.get_today_revenue())
            self.pending_exit = None
    
    @Slot()
    def _on_payment_cancelled(self):
        self.pending_exit = None
    
    @Slot(dict)
    def _on_exit_success(self, data: dict):
        pass
    
    def _show_card_manager(self):
        CardManagerDialog(self).exec()
    
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
    
    def closeEvent(self, event):
        self.mqtt_client.disconnect()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
