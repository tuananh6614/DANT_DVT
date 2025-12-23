"""
Parking Service - Xử lý nghiệp vụ vào/ra
"""

import logging
from typing import Optional, Tuple
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from src import database as db
from src.fee_calculator import calculate_fee

logger = logging.getLogger(__name__)


class ParkingService(QObject):
    """Service xử lý nghiệp vụ bãi xe"""
    
    # Signals
    entry_success = Signal(dict)      # {card_id, plate_number, slot_number}
    entry_failed = Signal(str)        # error message
    exit_ready = Signal(dict)         # {session, fee_info} - cần thanh toán
    exit_success = Signal(dict)       # {session, fee}
    exit_failed = Signal(str)         # error message
    slot_updated = Signal(dict)       # SlotStats
    
    def __init__(self, parent=None):
        super().__init__(parent)
        db.init_database()
    
    def process_entry(self, card_id: str) -> Tuple[bool, str]:
        """
        Xử lý xe vào
        Returns: (success, message)
        """
        logger.info(f"Processing entry for card: {card_id}")
        
        # Check thẻ hợp lệ
        card = db.get_card(card_id)
        if not card:
            msg = f"Thẻ {card_id} chưa đăng ký"
            logger.warning(msg)
            self.entry_failed.emit(msg)
            return False, msg
        
        # Check xe đã trong bãi chưa
        active_session = db.get_active_session(card_id)
        if active_session:
            msg = f"Thẻ {card_id} đang có xe trong bãi"
            logger.warning(msg)
            self.entry_failed.emit(msg)
            return False, msg
        
        # Check slot trống
        slot = db.get_available_slot()
        if slot is None:
            msg = "Bãi xe đã đầy"
            logger.warning(msg)
            self.entry_failed.emit(msg)
            return False, msg
        
        # Tạo session
        plate_number = card.get("plate_number", "")
        session_id = db.create_session(card_id, plate_number, slot)
        
        result = {
            "session_id": session_id,
            "card_id": card_id,
            "plate_number": plate_number,
            "slot_number": slot,
            "entry_time": datetime.now().strftime("%H:%M:%S")
        }
        
        logger.info(f"Entry success: {result}")
        self.entry_success.emit(result)
        self._emit_slot_update()
        
        return True, f"Xe vào slot {slot}"
    
    def process_exit(self, card_id: str) -> Tuple[bool, Optional[dict]]:
        """
        Xử lý xe ra - trả về thông tin để thanh toán
        Returns: (success, exit_info or None)
        """
        logger.info(f"Processing exit for card: {card_id}")
        
        # Tìm session đang active
        session = db.get_active_session(card_id)
        if not session:
            msg = f"Không tìm thấy xe với thẻ {card_id}"
            logger.warning(msg)
            self.exit_failed.emit(msg)
            return False, None
        
        # Tính tiền
        entry_time = session["entry_time"]
        fee_info = calculate_fee(entry_time)
        
        result = {
            "session": session,
            "fee_info": fee_info
        }
        
        logger.info(f"Exit ready: {result}")
        self.exit_ready.emit(result)
        
        return True, result
    
    def complete_exit(self, session_id: int, fee: int) -> bool:
        """Hoàn tất xe ra sau khi thanh toán"""
        success = db.complete_session(session_id, fee)
        if success:
            session = {"id": session_id, "fee": fee}
            self.exit_success.emit(session)
            self._emit_slot_update()
            logger.info(f"Exit completed: session {session_id}, fee {fee}")
        return success
    
    def _emit_slot_update(self):
        stats = db.get_slot_stats()
        self.slot_updated.emit(stats)
    
    def get_slot_stats(self) -> dict:
        return db.get_slot_stats()
    
    def get_recent_history(self, limit: int = 20) -> list:
        return db.get_recent_sessions(limit)
    
    def get_today_revenue(self) -> int:
        return db.get_today_revenue()
