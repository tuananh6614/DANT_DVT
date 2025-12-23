"""
Dashboard Widget - Giao diện chính
"""

from datetime import datetime
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)


class StatCard(QFrame):
    """Card hiển thị thống kê"""
    
    def __init__(self, title: str, value: str, color: str = "#667eea", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{color};border-radius:12px;}}")
        self.setFixedHeight(100)
        self.setMinimumWidth(200)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color:rgba(255,255,255,0.9);font-size:13px;background:transparent;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("color:white;font-size:26px;font-weight:bold;background:transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addStretch()
    
    def set_value(self, value: str):
        self.lbl_value.setText(value)


class DashboardWidget(QWidget):
    """Widget Dashboard chính"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet("QWidget{background:#1a1a2e;}")
        
        # Header
        header = QHBoxLayout()
        
        lbl_title = QLabel("🅿️ HỆ THỐNG QUẢN LÝ BÃI XE")
        lbl_title.setStyleSheet("font-size:18px;font-weight:bold;color:white;")
        
        self.lbl_mqtt_status = QLabel("MQTT: 🔴 Disconnected")
        self.lbl_mqtt_status.setStyleSheet("font-size:12px;color:#888;")
        
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(self.lbl_mqtt_status)
        
        # Stat Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.card_slots = StatCard("CHỖ TRỐNG", "0/10", "#667eea")
        self.card_vehicles = StatCard("XE TRONG BÃI", "0", "#00c853")
        self.card_revenue = StatCard("DOANH THU HÔM NAY", "0 VND", "#ff9800")
        
        cards_layout.addWidget(self.card_slots)
        cards_layout.addWidget(self.card_vehicles)
        cards_layout.addWidget(self.card_revenue)
        cards_layout.addStretch()
        
        # History Label
        lbl_history = QLabel("📋 LỊCH SỬ VÀO/RA")
        lbl_history.setStyleSheet("font-size:14px;font-weight:bold;color:white;margin-top:15px;")
        
        # History Table
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels(["Thời gian", "Loại", "Biển số", "Slot", "Phí"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.setStyleSheet("""
            QTableWidget {
                border:1px solid #333;
                border-radius:8px;
                background:#2d2d44;
                color:white;
                gridline-color:#444;
            }
            QHeaderView::section {
                background:#3d3d5c;
                color:white;
                padding:8px;
                border:none;
                font-weight:bold;
            }
            QTableWidget::item {
                padding:5px;
            }
            QTableWidget::item:alternate {
                background:#252538;
            }
        """)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_payment = QPushButton("💳 Thanh toán Online")
        self.btn_payment.setFixedHeight(42)
        self.btn_payment.setStyleSheet("""
            QPushButton {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #667eea,stop:1 #764ba2);
                color:white;border:none;border-radius:8px;font-size:13px;font-weight:bold;padding:0 20px;
            }
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5a6fd6,stop:1 #6a4190);}
        """)
        
        self.btn_cards = QPushButton("🎫 Quản lý thẻ")
        self.btn_cards.setFixedHeight(42)
        self.btn_cards.setStyleSheet("""
            QPushButton{background:#4a4a6a;color:white;border:none;border-radius:8px;font-size:13px;font-weight:bold;padding:0 20px;}
            QPushButton:hover{background:#5a5a7a;}
        """)
        
        self.btn_manual_entry = QPushButton("➡️ Xe vào")
        self.btn_manual_entry.setFixedHeight(42)
        self.btn_manual_entry.setStyleSheet("""
            QPushButton{background:#00c853;color:white;border:none;border-radius:8px;font-size:13px;font-weight:bold;padding:0 20px;}
            QPushButton:hover{background:#00a844;}
        """)
        
        self.btn_manual_exit = QPushButton("⬅️ Xe ra")
        self.btn_manual_exit.setFixedHeight(42)
        self.btn_manual_exit.setStyleSheet("""
            QPushButton{background:#ff9800;color:white;border:none;border-radius:8px;font-size:13px;font-weight:bold;padding:0 20px;}
            QPushButton:hover{background:#e68900;}
        """)
        
        btn_layout.addWidget(self.btn_payment)
        btn_layout.addWidget(self.btn_cards)
        btn_layout.addWidget(self.btn_manual_entry)
        btn_layout.addWidget(self.btn_manual_exit)
        btn_layout.addStretch()
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addLayout(header)
        layout.addLayout(cards_layout)
        layout.addWidget(lbl_history)
        layout.addWidget(self.table_history, 1)
        layout.addLayout(btn_layout)
    
    @Slot(bool)
    def set_mqtt_connected(self, connected: bool):
        if connected:
            self.lbl_mqtt_status.setText("MQTT: 🟢 Connected")
            self.lbl_mqtt_status.setStyleSheet("font-size:12px;color:#00c853;")
        else:
            self.lbl_mqtt_status.setText("MQTT: 🔴 Disconnected")
            self.lbl_mqtt_status.setStyleSheet("font-size:12px;color:#dc3545;")
    
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
    
    def add_history_entry(self, time_str: str, entry_type: str, plate: str, slot: str, fee: str):
        self.table_history.insertRow(0)
        
        self.table_history.setItem(0, 0, QTableWidgetItem(time_str))
        
        type_item = QTableWidgetItem(entry_type)
        if entry_type == "VÀO":
            type_item.setForeground(Qt.green)
        else:
            type_item.setForeground(Qt.red)
        self.table_history.setItem(0, 1, type_item)
        
        self.table_history.setItem(0, 2, QTableWidgetItem(plate))
        self.table_history.setItem(0, 3, QTableWidgetItem(slot))
        self.table_history.setItem(0, 4, QTableWidgetItem(fee))
        
        while self.table_history.rowCount() > 50:
            self.table_history.removeRow(self.table_history.rowCount() - 1)
    
    def load_history(self, sessions: list):
        self.table_history.setRowCount(0)
        for s in sessions:
            entry_time = s.get("entry_time", "")
            exit_time = s.get("exit_time")
            plate = s.get("plate_number", "N/A")
            slot = str(s.get("slot_number", ""))
            fee = f"{s.get('fee', 0):,}" if exit_time else "-"
            
            if exit_time:
                self.add_history_entry(str(exit_time)[:16], "RA", plate, slot, fee)
            self.add_history_entry(str(entry_time)[:16], "VÀO", plate, slot, "-")
