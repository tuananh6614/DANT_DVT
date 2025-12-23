"""
SEPAY CONFIGURATION

Cấu hình thanh toán SePay cho hệ thống desktop app
"""

from typing import Dict, Any

# API Configuration
SEPAY_CONFIG: Dict[str, Any] = {
    # API Configuration
    "api_url": "https://my.sepay.vn/userapi",
    "api_token": "6HZF6PEQDKSABI13CJADBESYRTNVLESHQNH7WKSBQMB4UPO9OG1XTJ9MCUR8PFRI",
    
    # QR Service - VietQR format (api.vietqr.io)
    "qr_url": "https://api.vietqr.io/v2/generate",
    
    # Bank Account Info - VietinBank
    "bank_short_name": "VTB",                     # VietinBank short code
    "bank_display_name": "VietinBank",            # Tên hiển thị ngân hàng
    "account_number": "106874512433",             # Số tài khoản
    "account_name": "DUONG VAN TUAN",             # Tên chủ tài khoản
    "acq_id": "970415",                           # VietinBank NAPAS code
    
    # System Settings
    "timeout": 30,                                # Timeout cho API calls (seconds)
    "polling_interval": 3,                        # Polling interval (seconds)
    
    # SEVQR PREFIX - Yêu cầu của SePay cho VietinBank
    "content_prefix": "SEVQR"                     # Prefix bắt buộc cho VietinBank
}

# Endpoint URLs
SEPAY_ENDPOINTS = {
    "transactions_list": "/transactions/list",      # Lấy danh sách giao dịch
    "transaction_detail": "/transactions/details",  # Chi tiết giao dịch
    "bankaccounts_list": "/bankaccounts/list",      # Danh sách tài khoản
    "bankaccount_detail": "/bankaccounts/details"   # Chi tiết tài khoản
}
