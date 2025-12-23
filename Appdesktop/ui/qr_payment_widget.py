"""
QR Payment Widget - Modern Design với Success Animation
"""

import base64
import logging

from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QWidget

from payment.sepay_helper import verify_payment

logger = logging.getLogger(__name__)


class CheckmarkWidget(QWidget):
    """Widget vẽ dấu tick với animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self._progress = 0.0
        self._circle_progress = 0.0
        
    def get_progress(self):
        return self._progress
    
    def set_progress(self, value):
        self._progress = value
        self.update()
    
    def get_circle_progress(self):
        return self._circle_progress
    
    def set_circle_progress(self, value):
        self._circle_progress = value
        self.update()
        
    progress = Property(float, get_progress, set_progress)
    circle_progress = Property(float, get_circle_progress, set_circle_progress)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx, cy = 75, 75
        radius = 60
        
        # Vẽ vòng tròn xanh
        pen = QPen(QColor("#ffffff"))
        pen.setWidth(8)
        painter.setPen(pen)
        
        if self._circle_progress > 0:
            span = int(self._circle_progress * 360 * 16)
            painter.drawArc(15, 15, 120, 120, 90 * 16, -span)
        
        # Vẽ dấu tick
        if self._progress > 0:
            pen.setWidth(8)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            p1 = (40, 75)
            p2 = (65, 100)
            p3 = (115, 50)
            
            if self._progress <= 0.4:
                t = self._progress / 0.4
                x = p1[0] + (p2[0] - p1[0]) * t
                y = p1[1] + (p2[1] - p1[1]) * t
                painter.drawLine(p1[0], p1[1], int(x), int(y))
            else:
                painter.drawLine(p1[0], p1[1], p2[0], p2[1])
                t = (self._progress - 0.4) / 0.6
                x = p2[0] + (p3[0] - p2[0]) * t
                y = p2[1] + (p3[1] - p2[1]) * t
                painter.drawLine(p2[0], p2[1], int(x), int(y))


class QRPaymentWidget(QDialog):
    payment_success = Signal(dict)
    payment_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.payment_info = {}
        self.verify_timer = QTimer(self)
        self.verify_timer.timeout.connect(self._check_payment)
        self.verify_interval = 5000
        self.max_verify_attempts = 60
        self.verify_count = 0
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("Thanh toán")
        self.setModal(True)
        self.setFixedSize(400, 620)
        self.setStyleSheet("QDialog{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #667eea,stop:1 #764ba2);}")

        # === QR View ===
        self.qr_container = QWidget()
        
        self.lbl_amount = QLabel("0 VND")
        self.lbl_amount.setAlignment(Qt.AlignCenter)
        self.lbl_amount.setStyleSheet("color:white;font-size:32px;font-weight:bold;")
        
        self.lbl_order = QLabel("Ma don: ---")
        self.lbl_order.setAlignment(Qt.AlignCenter)
        self.lbl_order.setStyleSheet("color:rgba(255,255,255,0.8);font-size:14px;")

        qr_card = QFrame()
        qr_card.setStyleSheet("QFrame{background:white;border-radius:16px;}")
        
        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignCenter)
        self.lbl_qr.setFixedSize(300, 300)
        
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(10, 10, 10, 10)
        qr_layout.addWidget(self.lbl_qr, 0, Qt.AlignCenter)

        self.lbl_status = QLabel("Dang cho thanh toan...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color:white;font-size:14px;font-weight:bold;padding:10px;background:rgba(0,0,0,0.2);border-radius:8px;")

        self.lbl_bank_info = QLabel()
        self.lbl_bank_info.setAlignment(Qt.AlignCenter)
        self.lbl_bank_info.setStyleSheet("color:white;font-size:11px;")
        self.lbl_bank_info.setWordWrap(True)

        btn_cancel = QPushButton("Huy thanh toan")
        btn_cancel.setFixedHeight(45)
        btn_cancel.setStyleSheet("QPushButton{background:rgba(255,255,255,0.2);color:white;border:2px solid rgba(255,255,255,0.5);border-radius:22px;font-size:14px;font-weight:bold;}QPushButton:hover{background:rgba(255,255,255,0.3);}")
        btn_cancel.clicked.connect(self._on_cancel)

        qr_view_layout = QVBoxLayout(self.qr_container)
        qr_view_layout.setContentsMargins(20, 20, 20, 20)
        qr_view_layout.setSpacing(12)
        qr_view_layout.addWidget(self.lbl_amount)
        qr_view_layout.addWidget(self.lbl_order)
        qr_view_layout.addWidget(qr_card, 0, Qt.AlignCenter)
        qr_view_layout.addWidget(self.lbl_status)
        qr_view_layout.addWidget(self.lbl_bank_info)
        qr_view_layout.addStretch()
        qr_view_layout.addWidget(btn_cancel)

        # === Success View ===
        self.success_container = QWidget()
        self.success_container.setStyleSheet("background:transparent;")
        self.success_container.hide()
        
        self.checkmark = CheckmarkWidget()
        
        lbl_success_title = QLabel("THANH TOAN THANH CONG!")
        lbl_success_title.setAlignment(Qt.AlignCenter)
        lbl_success_title.setStyleSheet("color:white;font-size:22px;font-weight:bold;")
        
        self.lbl_success_amount = QLabel("0 VND")
        self.lbl_success_amount.setAlignment(Qt.AlignCenter)
        self.lbl_success_amount.setStyleSheet("color:white;font-size:36px;font-weight:bold;")
        
        self.lbl_success_order = QLabel("Ma don: ---")
        self.lbl_success_order.setAlignment(Qt.AlignCenter)
        self.lbl_success_order.setStyleSheet("color:rgba(255,255,255,0.8);font-size:14px;")
        
        btn_done = QPushButton("Hoan tat")
        btn_done.setFixedSize(200, 50)
        btn_done.setStyleSheet("QPushButton{background:white;color:#667eea;border:none;border-radius:25px;font-size:16px;font-weight:bold;}QPushButton:hover{background:#f0f0f0;}")
        btn_done.clicked.connect(self.accept)
        
        success_layout = QVBoxLayout(self.success_container)
        success_layout.setContentsMargins(20, 60, 20, 40)
        success_layout.setSpacing(20)
        success_layout.addStretch()
        success_layout.addWidget(self.checkmark, 0, Qt.AlignCenter)
        success_layout.addWidget(lbl_success_title)
        success_layout.addWidget(self.lbl_success_amount)
        success_layout.addWidget(self.lbl_success_order)
        success_layout.addStretch()
        success_layout.addWidget(btn_done, 0, Qt.AlignCenter)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.qr_container)
        main_layout.addWidget(self.success_container)

    def display_payment(self, payment_data: dict):
        self.payment_info = payment_data
        self.verify_count = 0
        
        # Reset view
        self.qr_container.show()
        self.success_container.hide()
        
        amount = payment_data.get('amount', 0)
        self.lbl_amount.setText(f"{amount:,} VND")
        self.lbl_order.setText(f"Ma don: {payment_data.get('order_id', '')}")
        self.lbl_bank_info.setText(f"{payment_data.get('bank_name','')} | STK: {payment_data.get('account_number','')} | {payment_data.get('account_name','')}")
        
        qr_base64 = payment_data.get('qr_base64')
        if qr_base64:
            try:
                img_data = base64.b64decode(qr_base64)
                qimage = QImage.fromData(img_data)
                if not qimage.isNull():
                    pixmap = QPixmap.fromImage(qimage)
                    self.lbl_qr.setPixmap(pixmap.scaled(290, 290, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception as e:
                logger.error(f"QR error: {e}")
        
        self.lbl_status.setText("Dang cho thanh toan...")
        self.lbl_status.setStyleSheet("color:white;font-size:14px;font-weight:bold;padding:10px;background:rgba(0,0,0,0.2);border-radius:8px;")
        self.verify_timer.start(self.verify_interval)
        self.show()

    def _check_payment(self):
        self.verify_count += 1
        if self.verify_count > self.max_verify_attempts:
            self.verify_timer.stop()
            self.lbl_status.setText("Het thoi gian cho")
            self.lbl_status.setStyleSheet("color:white;font-size:14px;font-weight:bold;padding:10px;background:rgba(220,53,69,0.8);border-radius:8px;")
            return
        
        result = verify_payment(self.payment_info.get('amount', 0), self.payment_info.get('order_id', ''))
        if result:
            self.verify_timer.stop()
            self._show_success()
            self.payment_success.emit(result)

    def _show_success(self):
        """Chuyển sang màn hình thành công với animation"""
        # Cập nhật thông tin
        amount = self.payment_info.get('amount', 0)
        self.lbl_success_amount.setText(f"{amount:,} VND")
        self.lbl_success_order.setText(f"Ma don: {self.payment_info.get('order_id', '')}")
        
        # Đổi màu nền sang xanh
        self.setStyleSheet("QDialog{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #00c853,stop:1 #00a844);}")
        
        # Ẩn QR, hiện Success
        self.qr_container.hide()
        self.success_container.show()
        
        # Reset animation
        self.checkmark._progress = 0.0
        self.checkmark._circle_progress = 0.0
        
        # Chạy animation
        self.circle_anim = QPropertyAnimation(self.checkmark, b"circle_progress")
        self.circle_anim.setDuration(600)
        self.circle_anim.setStartValue(0.0)
        self.circle_anim.setEndValue(1.0)
        self.circle_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.check_anim = QPropertyAnimation(self.checkmark, b"progress")
        self.check_anim.setDuration(500)
        self.check_anim.setStartValue(0.0)
        self.check_anim.setEndValue(1.0)
        self.check_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.circle_anim.start()
        QTimer.singleShot(400, self.check_anim.start)

    def _on_cancel(self):
        self.verify_timer.stop()
        self.payment_cancelled.emit()
        self.reject()

    def closeEvent(self, event):
        self.verify_timer.stop()
        super().closeEvent(event)
