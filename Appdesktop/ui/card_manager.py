"""
Card Manager - Quản lý thẻ RFID
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFormLayout
)

from src import database as db


class CardManagerDialog(QDialog):
    """Dialog quản lý thẻ RFID"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý thẻ RFID")
        self.setMinimumSize(600, 500)
        self._build_ui()
        self._load_cards()
    
    def _build_ui(self):
        # Add Card Form
        form_layout = QFormLayout()
        
        self.txt_card_id = QLineEdit()
        self.txt_card_id.setPlaceholderText("Mã thẻ RFID")
        
        self.txt_owner = QLineEdit()
        self.txt_owner.setPlaceholderText("Tên chủ thẻ")
        
        self.txt_plate = QLineEdit()
        self.txt_plate.setPlaceholderText("Biển số xe")
        
        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("Số điện thoại")
        
        form_layout.addRow("Mã thẻ:", self.txt_card_id)
        form_layout.addRow("Chủ thẻ:", self.txt_owner)
        form_layout.addRow("Biển số:", self.txt_plate)
        form_layout.addRow("SĐT:", self.txt_phone)
        
        btn_add = QPushButton("➕ Thêm thẻ")
        btn_add.setStyleSheet("""
            QPushButton {
                background: #00c853;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background: #00a844; }
        """)
        btn_add.clicked.connect(self._add_card)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Mã thẻ", "Chủ thẻ", "Biển số", "SĐT", "Xóa"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(btn_add)
        layout.addWidget(QLabel("Danh sách thẻ:"))
        layout.addWidget(self.table, 1)
    
    def _load_cards(self):
        self.table.setRowCount(0)
        cards = db.get_all_cards()
        
        for card in cards:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(card["card_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(card["owner_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(card["plate_number"]))
            self.table.setItem(row, 3, QTableWidgetItem(card.get("phone", "")))
            
            btn_delete = QPushButton("🗑️")
            btn_delete.setStyleSheet("background: #dc3545; color: white; border: none; border-radius: 4px;")
            btn_delete.clicked.connect(lambda checked, cid=card["card_id"]: self._delete_card(cid))
            self.table.setCellWidget(row, 4, btn_delete)
    
    def _add_card(self):
        card_id = self.txt_card_id.text().strip()
        owner = self.txt_owner.text().strip()
        plate = self.txt_plate.text().strip()
        phone = self.txt_phone.text().strip()
        
        if not card_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mã thẻ")
            return
        
        if db.add_card(card_id, owner, plate, phone):
            self._clear_form()
            self._load_cards()
            QMessageBox.information(self, "Thành công", "Đã thêm thẻ mới")
        else:
            QMessageBox.warning(self, "Lỗi", "Mã thẻ đã tồn tại")
    
    def _delete_card(self, card_id: str):
        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Xóa thẻ {card_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_card(card_id)
            self._load_cards()
    
    def _clear_form(self):
        self.txt_card_id.clear()
        self.txt_owner.clear()
        self.txt_plate.clear()
        self.txt_phone.clear()
