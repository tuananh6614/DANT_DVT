"""
SEPAY HELPER - Tạo QR và Verify Payment
"""

import base64
import logging
import time
from typing import Optional, Dict

import requests

from payment.sepay_config import SEPAY_CONFIG, SEPAY_ENDPOINTS

logger = logging.getLogger(__name__)


class SePay:
    def __init__(self):
        self.api_token = SEPAY_CONFIG['api_token']
        self.api_url = SEPAY_CONFIG['api_url']
        self.qr_url = SEPAY_CONFIG['qr_url']
        self.account_number = SEPAY_CONFIG['account_number']
        self.account_name = SEPAY_CONFIG['account_name']
        self.acq_id = SEPAY_CONFIG['acq_id']

    def _make_api_request(self, endpoint, params=None) -> Dict:
        """Gửi GET request đến SePay API"""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = self.api_url + endpoint

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("SePay API Error: %s", response.text)
                return {'status': response.status_code, 'error': response.text}
        except Exception as e:
            logger.exception("SePay API Error: %s", e)
            return {'status': 500, 'error': str(e)}

    def generate_qr(self, amount: int, description: str) -> Optional[str]:
        """Tạo QR Code từ VietQR API, trả về base64 PNG"""
        payload = {
            "accountNo": self.account_number,
            "accountName": self.account_name,
            "acqId": self.acq_id,
            "amount": amount,
            "addInfo": description,
            "format": "text",
            "template": "compact"
        }
        
        try:
            response = requests.post(
                self.qr_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "00":
                    qr_data_url = data["data"]["qrDataURL"]
                    # Extract base64 from data URL
                    if "base64," in qr_data_url:
                        return qr_data_url.split("base64,")[1]
            return None
        except Exception as e:
            logger.error("VietQR error: %s", e)
            return None


    def verify_payment(self, amount: int, description: str, limit: int = 10) -> Optional[Dict]:
        """
        Verify payment bằng cách check API transactions
        Returns: Transaction info nếu tìm thấy, None nếu không
        """
        params = {'limit': limit, 'amount_in': amount}
        
        logger.info(f"[SePay] Verifying: amount={amount}, desc='{description}'")
        response = self._make_api_request(SEPAY_ENDPOINTS['transactions_list'], params)

        if response.get('status') == 200:
            transactions = response.get('transactions', [])
            for tx in transactions:
                tx_content = tx.get('transaction_content', '')
                if description.upper() in tx_content.upper():
                    logger.info(f"[SePay] ✅ MATCH: {tx}")
                    return tx
        
        logger.info("[SePay] ❌ No match found")
        return None

    def get_recent_transactions(self, limit: int = 20) -> Dict:
        """Lấy danh sách giao dịch gần đây"""
        return self._make_api_request(SEPAY_ENDPOINTS['transactions_list'], {'limit': limit})


# Global instance
sepay = SePay()


def create_payment(amount: int, order_id: str) -> Dict:
    """
    Tạo payment với QR code
    
    Returns:
        dict: {success, qr_base64, amount, order_id, description, bank_info}
    """
    description = f"{SEPAY_CONFIG['content_prefix']} {order_id}"
    
    qr_base64 = sepay.generate_qr(amount, description)
    
    if not qr_base64:
        return {'success': False, 'error': 'Failed to generate QR'}
    
    return {
        'success': True,
        'qr_base64': qr_base64,
        'amount': amount,
        'order_id': order_id,
        'description': description,
        'bank_name': SEPAY_CONFIG['bank_display_name'],
        'account_number': SEPAY_CONFIG['account_number'],
        'account_name': SEPAY_CONFIG['account_name']
    }


def verify_payment(amount: int, order_id: str) -> Optional[Dict]:
    """Verify payment theo order_id"""
    description = f"{SEPAY_CONFIG['content_prefix']} {order_id}"
    return sepay.verify_payment(amount, description)


if __name__ == '__main__':
    # Test
    result = create_payment(10000, "TEST001")
    print("Payment:", result.get('success'))
    if result.get('qr_base64'):
        print("QR length:", len(result['qr_base64']))
