"""
Success Dialog - Animation khi thanh toán thành công
"""

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QWidget, QGraphicsOpacityEffect


class CheckmarkWidget(QWidget):
    """Widget vẽ dấu tick với animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
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
        
        center_x, center_y = 60, 60
        radius = 50
        
        # Vẽ vòng tròn xanh
        pen = QPen(QColor("#00c853"))
        pen.setWidth(6)
        painter.setPen(pen)
        
        if self._circle_progress > 0:
            span = int(self._circle_progress * 360 * 16)
            painter.drawArc(10, 10, 100, 100, 90 * 16, -span)
        
        # Vẽ dấu tick
        if self._progress > 0:
            pen.setWidth(6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Điểm của dấu tick
            p1 = (30, 60)
            p2 = (50, 80)
            p3 = (90, 40)
            
            # Vẽ phần đầu của tick
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


class SuccessDialog(QDialog):
    """Dialog hiển thị khi thanh toán thành công"""
    
    def __init__(self, amount=0, order_id="", parent=None):
        super().__init__(parent)
        self.amount = amount
        self.order_id = order_id
        self._build_ui()
        
    def _build_ui(self):
        self.setWindowTitle("Thanh toán thành công")
        self.setModal(True)
        self.setFixedSize(350, 400)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00c853, stop:1 #00a844);
                border-radius: 20px;
            }
        """)
        
        # Checkmark
        self.checkmark = CheckmarkWidget()
        
        # Labels
        lbl_success = QLabel("THANH TOÁN THÀNH CÔNG")
        lbl_success.setAlignment(Qt.AlignCenter)
        lbl_success.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent;")
        
        self.lbl_amount = QLabel(f"{self.amount:,} VNĐ")
        self.lbl_amount.setAlignment(Qt.AlignCenter)
        self.lbl_amount.setStyleSheet("color: white; font-size: 32px; font-weight: bold; background: transparent;")
        
        self.lbl_order = QLabel(f"Mã đơn: {self.order_id}")
        self.lbl_order.setAlignment(Qt.AlignCenter)
        self.lbl_order.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 14px; background: transparent;")
        
        # OK Button
        btn_ok = QPushButton("Hoàn tất")
        btn_ok.setFixedSize(200, 45)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background: white;
                color: #00c853;
                border: none;
                border-radius: 22px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
        """)
        btn_ok.clicked.connect(self.accept)
        
        # Layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 40, 30, 30)
        layout.setSpacing(15)
        layout.addWidget(self.checkmark, 0, Qt.AlignCenter)
        layout.addWidget(lbl_success)
        layout.addWidget(self.lbl_amount)
        layout.addWidget(self.lbl_order)
        layout.addStretch()
        layout.addWidget(btn_ok, 0, Qt.AlignCenter)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
    def showEvent(self, event):
        super().showEvent(event)
        self._start_animation()
        
    def _start_animation(self):
        # Animation vòng tròn
        self.circle_anim = QPropertyAnimation(self.checkmark, b"circle_progress")
        self.circle_anim.setDuration(500)
        self.circle_anim.setStartValue(0.0)
        self.circle_anim.setEndValue(1.0)
        self.circle_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Animation dấu tick
        self.check_anim = QPropertyAnimation(self.checkmark, b"progress")
        self.check_anim.setDuration(400)
        self.check_anim.setStartValue(0.0)
        self.check_anim.setEndValue(1.0)
        self.check_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.circle_anim.start()
        QTimer.singleShot(300, self.check_anim.start)
    
    def set_payment_info(self, amount, order_id):
        self.amount = amount
        self.order_id = order_id
        self.lbl_amount.setText(f"{amount:,} VNĐ")
        self.lbl_order.setText(f"Mã đơn: {order_id}")
