"""
MQTT Client - Kết nối ESP32 (Compatible với paho-mqtt v2.x)
"""

import json
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, QTimer, QThread
import paho.mqtt.client as mqtt

from src.config import MQTT_CONFIG, MQTT_TOPICS

logger = logging.getLogger(__name__)


class MQTTWorker(QThread):
    """Worker thread cho MQTT để tránh blocking main thread"""
    
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str, dict)  # topic, payload
    error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client: Optional[mqtt.Client] = None
        self._running = False
    
    def run(self):
        self._running = True
        try:
            # Tạo client với callback_api_version cho paho-mqtt v2.x
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=MQTT_CONFIG["client_id"]
            )
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            if MQTT_CONFIG["username"]:
                self.client.username_pw_set(MQTT_CONFIG["username"], MQTT_CONFIG["password"])
            
            self.client.connect(
                MQTT_CONFIG["broker"],
                MQTT_CONFIG["port"],
                MQTT_CONFIG["keepalive"]
            )
            
            while self._running:
                self.client.loop(timeout=1.0)
                
        except Exception as e:
            logger.error(f"MQTT error: {e}")
            self.error.emit(str(e))
    
    def stop(self):
        self._running = False
        if self.client:
            self.client.disconnect()
        self.wait()
    
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("MQTT connected successfully")
            logger.info(f"Subscribing to: {MQTT_TOPICS['entry_card']}")
            client.subscribe(MQTT_TOPICS["entry_card"])
            logger.info(f"Subscribing to: {MQTT_TOPICS['exit_card']}")
            client.subscribe(MQTT_TOPICS["exit_card"])
            logger.info(f"Subscribing to: {MQTT_TOPICS['esp32_heartbeat']}")
            client.subscribe(MQTT_TOPICS["esp32_heartbeat"])
            client.subscribe(MQTT_TOPICS["slot_status"])
            client.subscribe(MQTT_TOPICS["slot_change"])
            self.connected.emit()
        else:
            logger.error(f"MQTT connect failed: {reason_code}")
            self.error.emit(f"Connect failed: {reason_code}")
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        logger.warning(f"MQTT disconnected: {reason_code}")
        self.disconnected.emit()
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload_str = msg.payload.decode()
            logger.info(f"[MQTT RAW] Topic: {topic}, Payload: {payload_str}")
            payload = json.loads(payload_str)
            self.message_received.emit(topic, payload)
        except Exception as e:
            logger.error(f"MQTT message error: {e}")
    
    def publish(self, topic: str, payload: dict):
        if self.client and self._running:
            self.client.publish(topic, json.dumps(payload))


class MQTTClient(QObject):
    """MQTT Client wrapper với Qt Signals"""
    
    connected = Signal()
    disconnected = Signal()
    error = Signal(str)
    entry_card_detected = Signal(str)
    exit_card_detected = Signal(str)
    esp32_heartbeat = Signal(dict)  # ESP32 heartbeat signal
    slot_status_updated = Signal(dict)  # Trạng thái tất cả slot
    slot_changed = Signal(int, bool)  # slot number, occupied
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[MQTTWorker] = None
        self._is_connected = False
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.connect)
    
    def connect(self):
        if self.worker and self.worker.isRunning():
            return
        
        self.reconnect_timer.stop()
        
        self.worker = MQTTWorker()
        self.worker.connected.connect(self._on_connected)
        self.worker.disconnected.connect(self._on_disconnected)
        self.worker.message_received.connect(self._on_message)
        self.worker.error.connect(self._on_error)
        self.worker.start()
        
        logger.info(f"Connecting to MQTT broker {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
    
    def disconnect(self):
        self.reconnect_timer.stop()
        if self.worker:
            self.worker.stop()
            self.worker = None
        self._is_connected = False
    
    def _on_connected(self):
        self._is_connected = True
        self.connected.emit()
    
    def _on_disconnected(self):
        self._is_connected = False
        self.disconnected.emit()
        # Auto reconnect sau 5s
        if not self.reconnect_timer.isActive():
            self.reconnect_timer.start(5000)
    
    def _on_message(self, topic: str, payload: dict):
        logger.info(f"[MQTTClient] Received: {topic} -> {payload}")
        
        if topic == MQTT_TOPICS["entry_card"]:
            card_id = payload.get("card_id", "")
            if card_id:
                self.entry_card_detected.emit(card_id)
        elif topic == MQTT_TOPICS["exit_card"]:
            card_id = payload.get("card_id", "")
            if card_id:
                self.exit_card_detected.emit(card_id)
        elif topic == MQTT_TOPICS["esp32_heartbeat"]:
            logger.info(f"[ESP32 HEARTBEAT] Received: {payload}")
            self.esp32_heartbeat.emit(payload)
        elif topic == MQTT_TOPICS["slot_status"]:
            logger.info(f"[SLOT STATUS] Received: {payload}")
            self.slot_status_updated.emit(payload)
        elif topic == MQTT_TOPICS["slot_change"]:
            slot = payload.get("slot", 0)
            occupied = payload.get("occupied", False)
            logger.info(f"[SLOT CHANGE] Slot {slot}: {'Occupied' if occupied else 'Available'}")
            self.slot_changed.emit(slot, occupied)
    
    def _on_error(self, msg: str):
        self.error.emit(msg)
        if not self.reconnect_timer.isActive():
            self.reconnect_timer.start(5000)
    
    def publish(self, topic: str, payload: dict):
        if self.worker:
            self.worker.publish(topic, payload)
            logger.info(f"MQTT publish: {topic} -> {payload}")
    
    def open_entry_barrier(self):
        self.publish(MQTT_TOPICS["entry_open"], {"action": "open"})
    
    def open_exit_barrier(self):
        self.publish(MQTT_TOPICS["exit_open"], {"action": "open"})
    
    def send_status(self, slots_available: int):
        self.publish(MQTT_TOPICS["status"], {"slots_available": slots_available})
    
    def send_lcd_entry(self, card_id: str, slot: int):
        """Gửi thông báo xe vào hiển thị trên LCD"""
        self.publish(MQTT_TOPICS["lcd_entry"], {"card_id": card_id, "slot": slot})
    
    def send_lcd_exit(self, card_id: str, fee: int):
        """Gửi thông báo xe ra hiển thị trên LCD"""
        self.publish(MQTT_TOPICS["lcd_exit"], {"card_id": card_id, "fee": fee})
    
    def send_lcd_error(self, message: str):
        """Gửi thông báo lỗi hiển thị trên LCD"""
        self.publish(MQTT_TOPICS["lcd_error"], {"message": message})
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
