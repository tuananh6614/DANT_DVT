"""
Fee Calculator - Tính tiền gửi xe
"""

import math
from datetime import datetime
from src.config import PARKING_CONFIG


def calculate_fee(entry_time: datetime, exit_time: datetime = None) -> dict:
    """
    Tính phí gửi xe
    
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
    
    # Miễn phí nếu dưới free_minutes
    if duration_minutes <= PARKING_CONFIG["free_minutes"]:
        return {
            "fee": 0,
            "duration_minutes": duration_minutes,
            "hours_charged": 0,
            "breakdown": "Miễn phí (dưới 15 phút)"
        }
    
    # Tính số giờ (làm tròn lên)
    hours = math.ceil(duration_minutes / 60)
    fee = hours * PARKING_CONFIG["hourly_rate"]
    
    # Đảm bảo phí tối thiểu
    fee = max(fee, PARKING_CONFIG["min_fee"])
    
    return {
        "fee": fee,
        "duration_minutes": duration_minutes,
        "hours_charged": hours,
        "breakdown": f"{hours} giờ x {PARKING_CONFIG['hourly_rate']:,} = {fee:,} VND"
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
