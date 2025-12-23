"""
Dashboard Widget - Giao diện chính (Professional UI)
"""

from datetime import datetime
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout
)


class StatCard(QFrame):
    """Card hiển thị thống kê"""
    
    def __init__(self, title: str, value: str, color: str = "#667eea", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{color};border-radius:10px;}}")
        self.setFixedHeight(90)
        self.setMinimumWidth(180)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color:rgba(255,255,255,0.85);font-size:12px;background:transparent;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("color:white;font-size:26px;font-weight:bold;background:transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addStretch()
    
    def set_value(self, value: str):
        self.lbl_value.setText(value)


class SlotCard(QFrame):
    """Card hiển thị slot đỗ xe"""
    
    def __init__(self, slot_id: int, parent=None):
        super().__init__(parent)
        self.slot_id = slot_id
        self.occupied = False
        
        self.setFixedSize(100, 60)
        self._update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        
        self.lbl_name = QLabel(f"Slot {slot_id}")
        self.lbl_name.setStyleSheet("color:white;font-size:13px;font-weight:bold;background:transparent;")
        self.lbl_name.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.lbl_name)
    
    def set_occupied(self, occupied: bool):
        self.occupied = occupied
        self._update_style()
    
    def _update_style(self):
        if self.occupied:
            self.setStyleSheet("QFrame{background:#c0392b;border-radius:6px;border:2px solid #e74c3c;}")
        else:
            self.setStyleSheet("QFrame{background:#27ae60;border-radius:6px;border:2px solid #2ecc71;}")


class DashboardWidget(QWidget):
    """Widget Dashboard chính"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slot_cards = []
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet("QWidget{background:#1a1a2e;}")
        
        # Header
        header = QHBoxLayout()
        
        lbl_title = QLabel("HE THONG QUAN LY BAI XE")
        lbl_title.setStyleSheet("font-size:18px;font-weight:bold;color:#4ade80;letter-spacing:2px;")
        
        # Status indicators
        status_layout = QHBoxLayout()
        status_layout.setSpacing(25)
        
        self.lbl_mqtt_status = QLabel("MQTT: Disconnected")
        self.lbl_mqtt_status.setStyleSheet("font-size:12px;color:#e74c3c;padding:5px 10px;background:#2d2d44;border-radius:4px;")
        
        self.lbl_esp32_status = QLabel("ESP32: Offline")
        self.lbl_esp32_status.setStyleSheet("font-size:12px;color:#e74c3c;padding:5px 10px;background:#2d2d44;border-radius:4px;")
        
        status_layout.addWidget(self.lbl_mqtt_status)
        status_layout.addWidget(self.lbl_esp32_status)
        
        header.addWidget(lbl_title)
        header.addStretch()
        header.addLayout(status_layout)
        
        # Stat Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.card_slots = StatCard("CHO TRONG", "3/3", "#3498db")
        self.card_vehicles = StatCard("XE TRONG BAI", "0", "#e67e22")
        self.card_revenue = StatCard("DOANH THU HOM NAY", "0 VND", "#9b59b6")
        
        cards_layout.addWidget(self.card_slots)
        cards_layout.addWidget(self.card_vehicles)
        cards_layout.addWidget(self.card_revenue)
        cards_layout.addStretch()

        # Parking Status - 2 columns: Available & Occupied
        parking_frame = QFrame()
        parking_frame.setStyleSheet("QFrame{background:#2d2d44;border-radius:10px;}")
        parking_layout = QHBoxLayout(parking_frame)
        parking_layout.setContentsMargins(15, 12, 15, 12)
        parking_layout.setSpacing(20)
        
        # Available slots column
        available_col = QVBoxLayout()
        available_col.setSpacing(8)
        
        lbl_available = QLabel("CHO TRONG")
        lbl_available.setStyleSheet("color:#2ecc71;font-size:12px;font-weight:bold;background:transparent;")
        available_col.addWidget(lbl_available)
        
        self.available_slots_layout = QHBoxLayout()
        self.available_slots_layout.setSpacing(8)
        available_col.addLayout(self.available_slots_layout)
        available_col.addStretch()
        
        # Occupied slots column
        occupied_col = QVBoxLayout()
        occupied_col.setSpacing(8)
        
        lbl_occupied = QLabel("CO XE")
        lbl_occupied.setStyleSheet("color:#e74c3c;font-size:12px;font-weight:bold;background:transparent;")
        occupied_col.addWidget(lbl_occupied)
        
        self.occupied_slots_layout = QHBoxLayout()
        self.occupied_slots_layout.setSpacing(8)
        occupied_col.addLayout(self.occupied_slots_layout)
        occupied_col.addStretch()
        
        # Separator
        separator = QFrame()
        separator.setFixedWidth(2)
        separator.setStyleSheet("background:#444;")
        
        parking_layout.addLayout(available_col, 1)
        parking_layout.addWidget(separator)
        parking_layout.addLayout(occupied_col, 1)
        
        # Create slot cards
        for i in range(3):
            card = SlotCard(i + 1)
            self.slot_cards.append(card)
            self.available_slots_layout.addWidget(card)
        
        self.available_slots_layout.addStretch()
        self.occupied_slots_layout.addStretch()
        
        # History Table - Improved Design
        history_header = QHBoxLayout()
        lbl_history = QLabel("LICH SU VAO / RA")
        lbl_history.setStyleSheet("font-size:14px;font-weight:bold;color:#4ade80;margin-top:8px;")
        history_header.addWidget(lbl_history)
        history_header.addStretch()
        
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels(["Thoi gian", "Trang thai", "Ma the", "Slot", "Phi"])
        
        # Set column widths
        header_view = self.table_history.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.Fixed)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.Fixed)
        header_view.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.table_history.setColumnWidth(0, 150)  # Thoi gian
        self.table_history.setColumnWidth(1, 100)  # Trang thai
        self.table_history.setColumnWidth(3, 70)   # Slot
        self.table_history.setColumnWidth(4, 120)  # Phi
        
        self.table_history.setAlternatingRowColors(True)
        self.table_history.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_history.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setShowGrid(False)
        
        self.table_history.setStyleSheet("""
            QTableWidget {
                border: none;
                border-radius: 10px;
                background: #2d2d44;
                color: white;
                font-size: 13px;
            }
            QHeaderView::section {
                background: #3d3d5c;
                color: #aaa;
                padding: 10px 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d5c;
            }
            QTableWidget::item:alternate {
                background: #252540;
            }
            QTableWidget::item:selected {
                background: #4a4a6a;
            }
        """)

        # Buttons - Simplified (removed Xe vao, Xe ra)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        btn_style = """
            QPushButton {
                background: %s;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: %s;
            }
        """
        
        self.btn_payment = QPushButton("Thanh toan")
        self.btn_payment.setStyleSheet(btn_style % ("#3498db", "#2980b9"))
        
        self.btn_cards = QPushButton("Quan ly the")
        self.btn_cards.setStyleSheet(btn_style % ("#7f8c8d", "#6c7a7b"))
        
        # Hidden buttons for compatibility (not shown in UI)
        self.btn_manual_entry = QPushButton()
        self.btn_manual_entry.hide()
        self.btn_manual_exit = QPushButton()
        self.btn_manual_exit.hide()
        
        self.btn_reset = QPushButton("Reset du lieu")
        self.btn_reset.setStyleSheet(btn_style % ("#c0392b", "#a93226"))
        
        btn_layout.addWidget(self.btn_payment)
        btn_layout.addWidget(self.btn_cards)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_reset)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addLayout(header)
        layout.addLayout(cards_layout)
        layout.addWidget(parking_frame)
        layout.addLayout(history_header)
        layout.addWidget(self.table_history, 1)
        layout.addLayout(btn_layout)
    
    def _reorganize_slots(self):
        """Di chuyển slot cards giữa 2 cột dựa trên trạng thái"""
        for card in self.slot_cards:
            self.available_slots_layout.removeWidget(card)
            self.occupied_slots_layout.removeWidget(card)
        
        for card in self.slot_cards:
            if card.occupied:
                self.occupied_slots_layout.insertWidget(
                    self.occupied_slots_layout.count() - 1, card
                )
            else:
                self.available_slots_layout.insertWidget(
                    self.available_slots_layout.count() - 1, card
                )
    
    @Slot(bool)
    def set_mqtt_connected(self, connected: bool):
        if connected:
            self.lbl_mqtt_status.setText("MQTT: Connected")
            self.lbl_mqtt_status.setStyleSheet("font-size:12px;color:#2ecc71;padding:5px 10px;background:#2d2d44;border-radius:4px;")
        else:
            self.lbl_mqtt_status.setText("MQTT: Disconnected")
            self.lbl_mqtt_status.setStyleSheet("font-size:12px;color:#e74c3c;padding:5px 10px;background:#2d2d44;border-radius:4px;")
    
    @Slot(dict)
    def set_esp32_status(self, data: dict):
        online = data.get("online", False)
        ip = data.get("ip", "")
        
        if online:
            text = f"ESP32: Online"
            if ip:
                text += f" ({ip})"
            self.lbl_esp32_status.setText(text)
            self.lbl_esp32_status.setStyleSheet("font-size:12px;color:#2ecc71;padding:5px 10px;background:#2d2d44;border-radius:4px;")
        else:
            self.lbl_esp32_status.setText("ESP32: Offline")
            self.lbl_esp32_status.setStyleSheet("font-size:12px;color:#e74c3c;padding:5px 10px;background:#2d2d44;border-radius:4px;")
    
    def set_esp32_offline(self):
        self.lbl_esp32_status.setText("ESP32: Offline")
        self.lbl_esp32_status.setStyleSheet("font-size:12px;color:#e74c3c;padding:5px 10px;background:#2d2d44;border-radius:4px;")

    @Slot(dict)
    def update_slot_stats(self, stats: dict):
        total = stats.get("total", 0)
        available = stats.get("available", 0)
        occupied = stats.get("occupied", 0)
        
        self.card_slots.set_value(f"{available}/{total}")
        self.card_vehicles.set_value(str(occupied))
    
    @Slot(int)
    def update_revenue(self, revenue: int):
        self.card_revenue.set_value(f"{revenue:,} VND")
    
    def add_history_entry(self, time_str: str, entry_type: str, card_id: str, plate: str, slot: str, fee: str):
        """Thêm entry vào bảng lịch sử với giao diện đẹp hơn"""
        self.table_history.insertRow(0)
        
        # Thời gian
        time_item = QTableWidgetItem(time_str)
        time_item.setTextAlignment(Qt.AlignCenter)
        self.table_history.setItem(0, 0, time_item)
        
        # Trạng thái với màu sắc và icon
        if entry_type == "VÀO":
            status_text = "VAO"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("#4ade80"))  # Green
        else:
            status_text = "RA"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("#f87171"))  # Red
        
        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setFont(QFont("", -1, QFont.Bold))
        self.table_history.setItem(0, 1, status_item)
        
        # Mã thẻ
        card_item = QTableWidgetItem(card_id)
        card_item.setForeground(QColor("#60a5fa"))  # Blue
        self.table_history.setItem(0, 2, card_item)
        
        # Slot
        slot_item = QTableWidgetItem(slot if slot and slot != "-" else "-")
        slot_item.setTextAlignment(Qt.AlignCenter)
        self.table_history.setItem(0, 3, slot_item)
        
        # Phí
        fee_item = QTableWidgetItem(fee if fee and fee != "-" else "-")
        fee_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if fee and fee != "-" and fee != "0":
            fee_item.setForeground(QColor("#fbbf24"))  # Yellow/Gold
        self.table_history.setItem(0, 4, fee_item)
        
        # Set row height
        self.table_history.setRowHeight(0, 40)
        
        # Giới hạn số dòng
        while self.table_history.rowCount() > 50:
            self.table_history.removeRow(self.table_history.rowCount() - 1)
    
    def load_history(self, sessions: list):
        self.table_history.setRowCount(0)
        for s in sessions:
            entry_time = s.get("entry_time", "")
            exit_time = s.get("exit_time")
            card_id = s.get("card_id", "N/A")
            plate = s.get("plate_number", "N/A")
            slot = str(s.get("slot_number", "")) if s.get("slot_number") else "-"
            fee = f"{s.get('fee', 0):,}" if exit_time and s.get('fee', 0) > 0 else "-"
            
            if exit_time:
                self.add_history_entry(str(exit_time)[:16], "RA", card_id, plate, "-", fee)
            self.add_history_entry(str(entry_time)[:16], "VÀO", card_id, plate, slot, "-")
    
    @Slot(int, bool)
    def update_slot(self, slot: int, occupied: bool):
        if slot < 1 or slot > len(self.slot_cards):
            return
        
        card = self.slot_cards[slot - 1]
        card.set_occupied(occupied)
        self._reorganize_slots()
        self._update_sensor_stats()
    
    def _update_sensor_stats(self):
        total = len(self.slot_cards)
        occupied = sum(1 for c in self.slot_cards if c.occupied)
        available = total - occupied
        
        self.card_slots.set_value(f"{available}/{total}")
        self.card_vehicles.set_value(str(occupied))
    
    @Slot(dict)
    def update_all_slots(self, data: dict):
        slots = data.get("slots", [])
        for i, occupied in enumerate(slots):
            if i < len(self.slot_cards):
                self.slot_cards[i].set_occupied(occupied)
        
        self._reorganize_slots()
        self._update_sensor_stats()
