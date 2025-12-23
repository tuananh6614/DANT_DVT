"""
Fee Calculator - Tính tiền gửi xe
"""

import math
from datetime import datetime
from src.config import PARKING_CONFIG


def calculate_fee(entry_time: datetime, exit_time: datetime = None) -> dict:
    """
    Tính phí gửi xe
    Phí mặc định: 3000 VND khi vào
    
    Returns:
        dict: {fee, duration_minutes, hours_charged, breakdown}
    """
    if exit_time is None:
        exit_time = datetime.now()
    
    # Parse entry_time nếu là string
    if isinstance(entry_time, str):
        entry_time = datetime.fromisoformat(entry_time)
    
    duration = exit_time - entry_time
    duration_minutes = int(duration.total_seconds() / 60)
    
    # Phí mặc định 3000 VND
    base_fee = 3000
    
    return {
        "fee": base_fee,
        "duration_minutes": duration_minutes,
        "hours_charged": 0,
        "breakdown": f"Phí gửi xe: {base_fee:,} VND"
    }


def format_duration(minutes: int) -> str:
    """Format thời gian đẹp"""
    if minutes < 60:
        return f"{minutes} phút"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours} giờ"
    return f"{hours} giờ {mins} phút"
