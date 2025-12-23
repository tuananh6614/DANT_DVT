"""
Card Manager - Quản lý thẻ RFID với màn hình quẹt thẻ
"""

from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QWidget, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont, QPainter, QColor, QPen

from src import database as db


class SuccessAnimation(QWidget):
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self._progress = 0
        self._check_progress = 0
        self._scale = 1.0
        
        self.circle_anim = QPropertyAnimation(self, b"progress")
        self.circle_anim.setDuration(300)
        self.circle_anim.setStartValue(0)
        self.circle_anim.setEndValue(100)
        self.circle_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.check_anim = QPropertyAnimation(self, b"check_progress")
        self.check_anim.setDuration(250)
        self.check_anim.setStartValue(0)
        self.check_anim.setEndValue(100)
        self.check_anim.setEasingCurve(QEasingCurve.OutBack)
        
        self.scale_anim = QPropertyAnimation(self, b"scale")
        self.scale_anim.setDuration(150)
        self.scale_anim.setStartValue(0.8)
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.setEasingCurve(QEasingCurve.OutBack)
        
        self.circle_anim.finished.connect(self.check_anim.start)
        self.check_anim.finished.connect(self._on_check_done)
    
    def _on_check_done(self):
        QTimer.singleShot(600, self._emit_finished)
    
    def _emit_finished(self):
        self.finished.emit()
    
    def start(self):
        self._progress = 0
        self._check_progress = 0
        self._scale = 0.8
        self.scale_anim.start()
        self.circle_anim.start()
    
    def get_progress(self):
        return self._progress
    def set_progress(self, v):
        self._progress = v
        self.update()
    def get_check_progress(self):
        return self._check_progress
    def set_check_progress(self, v):
        self._check_progress = v
        self.update()
    def get_scale(self):
        return self._scale
    def set_scale(self, v):
        self._scale = v
        self.update()
    
    progress = Property(int, get_progress, set_progress)
    check_progress = Property(int, get_check_progress, set_check_progress)
    scale = Property(float, get_scale, set_scale)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2
        radius = 60
        painter.translate(cx, cy)
        painter.scale(self._scale, self._scale)
        painter.translate(-cx, -cy)
        
        # Background circle
        painter.setPen(QPen(QColor("#2d2d44"), 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
        # Progress arc
        if self._progress > 0:
            pen = QPen(QColor("#10b981"), 4)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            span = int(-self._progress * 3.6 * 16)
            painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 90 * 16, span)
        
        # Checkmark
        if self._check_progress > 0:
            pen = QPen(QColor("#10b981"), 5)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            p1, p2, p3 = (cx - 25, cy), (cx - 5, cy + 20), (cx + 30, cy - 18)
            prog = self._check_progress / 100.0
            if prog <= 0.4:
                t = prog / 0.4
                painter.drawLine(int(p1[0]), int(p1[1]), int(p1[0]+(p2[0]-p1[0])*t), int(p1[1]+(p2[1]-p1[1])*t))
            else:
                painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
                t = (prog - 0.4) / 0.6
                painter.drawLine(int(p2[0]), int(p2[1]), int(p2[0]+(p3[0]-p2[0])*t), int(p2[1]+(p3[1]-p2[1])*t))



class WaitingCardWidget(QWidget):
    card_registered = Signal(str)
    cancelled = Signal()
    
    def __init__(self, mqtt_client, parent=None):
        super().__init__(parent)
        self.mqtt_client = mqtt_client
        self._pulse_opacity = 1.0
        self._detected_card_id = None
        self._is_waiting = False
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet("background: #0f0f1a;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)
        
        # Icon RFID
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(140, 140)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("""
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.6,
                fx:0.5, fy:0.3, stop:0 #8b5cf6, stop:1 #6366f1);
            border-radius: 70px;
        """)
        self.opacity_effect = QGraphicsOpacityEffect(self.icon_label)
        self.icon_label.setGraphicsEffect(self.opacity_effect)
        
        # Success animation
        self.success_anim = SuccessAnimation()
        self.success_anim.hide()
        self.success_anim.finished.connect(self._on_anim_finished)
        
        # Title
        self.title = QLabel("CHO QUET THE")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: #fff; font-size: 22px; font-weight: bold; letter-spacing: 2px;")
        
        # Subtitle
        self.subtitle = QLabel("Dua the RFID vao dau doc VAO hoac RA")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("color: #9ca3af; font-size: 13px;")
        
        # Card ID label
        self.card_id_label = QLabel()
        self.card_id_label.setAlignment(Qt.AlignCenter)
        self.card_id_label.setStyleSheet("color: #10b981; font-size: 15px; font-weight: bold; font-family: Consolas;")
        self.card_id_label.hide()
        
        # Cancel button
        self.btn_cancel = QPushButton("Huy bo")
        self.btn_cancel.setFixedSize(120, 38)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #9ca3af; border: 2px solid #4b5563; border-radius: 19px; font-size: 13px; font-weight: 600; }
            QPushButton:hover { border-color: #ef4444; color: #ef4444; }
        """)
        self.btn_cancel.clicked.connect(self._on_cancel)
        
        layout.addStretch(2)
        layout.addWidget(self.icon_label, 0, Qt.AlignCenter)
        layout.addWidget(self.success_anim, 0, Qt.AlignCenter)
        layout.addSpacing(12)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.card_id_label)
        layout.addStretch(2)
        layout.addWidget(self.btn_cancel, 0, Qt.AlignCenter)
        layout.addStretch(1)
        
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse)
        self.pulse_dir = -1
    
    def _pulse(self):
        self._pulse_opacity += self.pulse_dir * 0.03
        if self._pulse_opacity <= 0.4:
            self.pulse_dir = 1
        elif self._pulse_opacity >= 1.0:
            self.pulse_dir = -1
        self.opacity_effect.setOpacity(self._pulse_opacity)
    
    def _on_cancel(self):
        self.stop_waiting()
        self.cancelled.emit()
    
    def start_waiting(self):
        self._is_waiting = True
        self._detected_card_id = None
        self.icon_label.show()
        self.success_anim.hide()
        self.title.setText("CHO QUET THE")
        self.title.setStyleSheet("color:#fff;font-size:22px;font-weight:bold;letter-spacing:2px;")
        self.subtitle.setText("Dua the RFID vao dau doc VAO hoac RA")
        self.subtitle.setStyleSheet("color:#9ca3af;font-size:13px;")
        self.card_id_label.hide()
        self.btn_cancel.show()
        self.pulse_timer.start(25)
        self._pulse_opacity = 1.0
        self.pulse_dir = -1
        
        if self.mqtt_client:
            try:
                self.mqtt_client.entry_card_detected.connect(self._on_card, Qt.UniqueConnection)
                self.mqtt_client.exit_card_detected.connect(self._on_card, Qt.UniqueConnection)
            except:
                pass
    
    def stop_waiting(self):
        self._is_waiting = False
        self.pulse_timer.stop()
        if self.mqtt_client:
            try:
                self.mqtt_client.entry_card_detected.disconnect(self._on_card)
            except:
                pass
            try:
                self.mqtt_client.exit_card_detected.disconnect(self._on_card)
            except:
                pass
    
    def _on_card(self, card_id: str):
        print(f"[WaitingCard] Card detected: {card_id}, is_waiting: {self._is_waiting}")
        if not self._is_waiting:
            return
        self._detected_card_id = card_id
        self._is_waiting = False
        self.pulse_timer.stop()
        
        self.icon_label.hide()
        self.success_anim.show()
        self.success_anim.start()
        
        self.title.setText("THANH CONG!")
        self.title.setStyleSheet("color:#10b981;font-size:22px;font-weight:bold;letter-spacing:2px;")
        self.subtitle.setText("The da duoc nhan dien")
        self.subtitle.setStyleSheet("color:#10b981;font-size:13px;")
        self.card_id_label.setText(f"Ma the: {card_id}")
        self.card_id_label.show()
        self.btn_cancel.hide()
    
    def _on_anim_finished(self):
        print(f"[WaitingCard] Animation finished, card_id: {self._detected_card_id}")
        if self._detected_card_id:
            self.card_registered.emit(self._detected_card_id)



class CardManagerDialog(QDialog):
    def __init__(self, parent=None, mqtt_client=None):
        super().__init__(parent)
        self.mqtt_client = mqtt_client
        if parent and hasattr(parent, 'mqtt_client'):
            self.mqtt_client = parent.mqtt_client
        self.setWindowTitle("Quan ly the RFID")
        self.setMinimumSize(700, 520)
        self.setStyleSheet("QDialog { background: #0f0f1a; } QLabel { color: #e5e7eb; }")
        self._build_ui()
        self._load_cards()
    
    def _build_ui(self):
        self.stack = QStackedWidget()
        self.list_page = QWidget()
        self._build_list_page()
        self.waiting_page = WaitingCardWidget(self.mqtt_client)
        self.waiting_page.card_registered.connect(self._on_card_registered)
        self.waiting_page.cancelled.connect(self._show_list)
        self.stack.addWidget(self.list_page)
        self.stack.addWidget(self.waiting_page)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
    
    def _build_list_page(self):
        layout = QVBoxLayout(self.list_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Quan ly the RFID")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f3f4f6;")
        self.btn_add = QPushButton("+ Them the moi")
        self.btn_add.setFixedHeight(40)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8b5cf6,stop:1 #6366f1); color: white; border: none; border-radius: 8px; padding: 0 20px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c3aed,stop:1 #4f46e5); }
        """)
        self.btn_add.clicked.connect(self._show_waiting)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_add)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Ma the", "Chu the", "Bien so", "SDT", ""])
        for i in range(4):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 60)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget { background: #1a1a2e; color: #e5e7eb; border: 1px solid #2d2d44; border-radius: 8px; font-size: 12px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #252540; }
            QTableWidget::item:selected { background: #3730a3; }
            QHeaderView::section { background: #1e1e32; color: #9ca3af; padding: 10px 8px; border: none; font-weight: 600; font-size: 11px; }
        """)
        
        self.stats_label = QLabel("Tong: 0 the")
        self.stats_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        
        layout.addLayout(header)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.stats_label)
    
    def _load_cards(self):
        self.table.setRowCount(0)
        cards = db.get_all_cards()
        for card in cards:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 44)
            
            item = QTableWidgetItem(card["card_id"])
            item.setFont(QFont("Consolas", 10))
            item.setForeground(QColor("#a78bfa"))
            self.table.setItem(row, 0, item)
            
            for col, key in [(1, "owner_name"), (2, "plate_number"), (3, "phone")]:
                val = card.get(key) or "-"
                item = QTableWidgetItem(val)
                if val == "-":
                    item.setForeground(QColor("#6b7280"))
                self.table.setItem(row, col, item)
            
            btn = QPushButton("X")
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: #dc2626; color: white; border: none; border-radius: 14px; font-size: 12px; font-weight: bold; }
                QPushButton:hover { background: #b91c1c; }
            """)
            btn.clicked.connect(lambda c, cid=card["card_id"]: self._delete_card(cid))
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.addWidget(btn, 0, Qt.AlignCenter)
            self.table.setCellWidget(row, 4, w)
        
        self.stats_label.setText(f"Tong: {len(cards)} the")
    
    def _show_waiting(self):
        self.stack.setCurrentWidget(self.waiting_page)
        self.waiting_page.start_waiting()
    
    def _show_list(self):
        self.waiting_page.stop_waiting()
        self.stack.setCurrentWidget(self.list_page)
    
    def _on_card_registered(self, card_id: str):
        print(f"[CardManager] Card registered: {card_id}")
        self.waiting_page.stop_waiting()
        
        # Check existing
        existing = db.get_card(card_id)
        print(f"[CardManager] Existing card: {existing}")
        if existing:
            self._show_list()
            QMessageBox.warning(self, "Thong bao", f"The {card_id} da ton tai!")
            return
        
        # Add new card
        result = db.add_card(card_id, "", "", "")
        print(f"[CardManager] Add card result: {result}")
        self._load_cards()
        self._show_list()
        QMessageBox.information(self, "Thanh cong", f"Da them the: {card_id}")
    
    def _delete_card(self, card_id: str):
        if QMessageBox.question(self, "Xac nhan", f"Xoa the {card_id}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            db.delete_card(card_id)
            self._load_cards()
    
    def closeEvent(self, event):
        self.waiting_page.stop_waiting()
        super().closeEvent(event)
