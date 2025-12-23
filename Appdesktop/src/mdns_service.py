"""
mDNS Service - Tự động phát hiện ESP32 và quảng bá MQTT Broker
Giúp ESP32 và App tự tìm nhau mà không cần biết IP cụ thể
"""

import socket
import logging
from typing import Optional, List, Tuple
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

logger = logging.getLogger(__name__)


class ESP32Listener(ServiceListener):
    """Listener để tìm ESP32 qua mDNS"""
    
    def __init__(self):
        self.devices: List[Tuple[str, str, int]] = []  # (name, ip, port)
    
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0]) if info.addresses else None
            if ip:
                self.devices.append((name, ip, info.port))
                logger.info(f"[mDNS] Found ESP32: {name} at {ip}:{info.port}")
    
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        logger.info(f"[mDNS] ESP32 removed: {name}")
    
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass


class MDNSService:
    """
    mDNS Service cho Parking System
    
    Chức năng:
    1. Quảng bá máy tính này là MQTT Broker (parking-broker.local)
    2. Tìm ESP32 trong mạng (parking-esp32.local)
    """
    
    def __init__(self):
        self.zeroconf: Optional[Zeroconf] = None
        self.broker_info: Optional[ServiceInfo] = None
        self.esp32_listener: Optional[ESP32Listener] = None
        self.browser: Optional[ServiceBrowser] = None
        self._local_ip: Optional[str] = None
    
    def get_local_ip(self) -> str:
        """Lấy IP local của máy tính"""
        if self._local_ip:
            return self._local_ip
        
        try:
            # Tạo socket để lấy IP thực
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            self._local_ip = "127.0.0.1"
        
        return self._local_ip
    
    def start(self, mqtt_port: int = 1883):
        """
        Khởi động mDNS service
        - Quảng bá MQTT broker
        - Bắt đầu tìm ESP32
        """
        try:
            self.zeroconf = Zeroconf()
            local_ip = self.get_local_ip()
            
            # Quảng bá MQTT Broker
            self.broker_info = ServiceInfo(
                "_mqtt._tcp.local.",
                "Parking MQTT Broker._mqtt._tcp.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=mqtt_port,
                properties={
                    "name": "parking-broker",
                    "version": "1.0"
                },
                server="parking-broker.local."
            )
            
            self.zeroconf.register_service(self.broker_info)
            logger.info(f"[mDNS] Registered MQTT broker at {local_ip}:{mqtt_port}")
            logger.info(f"[mDNS] Hostname: parking-broker.local")
            
            # Tìm ESP32
            self.esp32_listener = ESP32Listener()
            self.browser = ServiceBrowser(
                self.zeroconf, 
                "_parking._tcp.local.", 
                self.esp32_listener
            )
            logger.info("[mDNS] Started searching for ESP32 devices...")
            
            return True
            
        except Exception as e:
            logger.error(f"[mDNS] Failed to start: {e}")
            return False
    
    def stop(self):
        """Dừng mDNS service"""
        try:
            if self.broker_info and self.zeroconf:
                self.zeroconf.unregister_service(self.broker_info)
            if self.zeroconf:
                self.zeroconf.close()
            logger.info("[mDNS] Service stopped")
        except Exception as e:
            logger.error(f"[mDNS] Error stopping: {e}")
    
    def get_esp32_devices(self) -> List[Tuple[str, str, int]]:
        """Lấy danh sách ESP32 đã tìm thấy"""
        if self.esp32_listener:
            return self.esp32_listener.devices
        return []
    
    def find_esp32(self, timeout: float = 5.0) -> Optional[str]:
        """
        Tìm ESP32 trong mạng
        Returns: IP của ESP32 hoặc None
        """
        import time
        
        if not self.esp32_listener:
            return None
        
        # Đợi một chút để tìm
        start = time.time()
        while time.time() - start < timeout:
            if self.esp32_listener.devices:
                return self.esp32_listener.devices[0][1]  # Return IP
            time.sleep(0.5)
        
        return None


# Singleton instance
_mdns_service: Optional[MDNSService] = None


def get_mdns_service() -> MDNSService:
    """Lấy singleton instance của MDNSService"""
    global _mdns_service
    if _mdns_service is None:
        _mdns_service = MDNSService()
    return _mdns_service
