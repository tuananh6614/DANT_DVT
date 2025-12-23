/*
 * MQTT Client - Kết nối với App Desktop
 * File: mqtt_client.cpp
 * Tham khảo từ baidoxe project
 */

#include "../include/mqtt_client.h"

// Global instances (giống baidoxe)
WiFiClient espClient;
PubSubClient mqtt(espClient);

// Static instance for callback
MQTTClientManager* MQTTClientManager::_instance = nullptr;

MQTTClientManager::MQTTClientManager() {
    _instance = this;
    memset(_server, 0, sizeof(_server));
    _port = 1883;
    _lastHeartbeat = 0;
    _lastReconnect = 0;
    _entryOpenCallback = nullptr;
    _exitOpenCallback = nullptr;
    _lcdEntryCallback = nullptr;
    _lcdExitCallback = nullptr;
    _lcdErrorCallback = nullptr;
}

void MQTTClientManager::begin(const char* server, int port) {
    strncpy(_server, server, sizeof(_server) - 1);
    _port = port;
    
    // Giống baidoxe: setServer và setKeepAlive
    mqtt.setServer(_server, _port);
    mqtt.setKeepAlive(15);  // Giảm keepalive để tránh timeout
    mqtt.setCallback(_staticCallback);
    
    Serial.printf("[MQTT] Server: %s:%d\n", _server, _port);
    
    _connect();
}

void MQTTClientManager::_connect() {
    if (mqtt.connected()) return;
    
    Serial.print("[MQTT] Connecting...");
    String clientId = "esp32-parking-" + String(random(0xffff), HEX);
    
    if (mqtt.connect(clientId.c_str())) {
        Serial.println("connected!");
        
        // Subscribe các topic cần nhận
        mqtt.subscribe(TOPIC_ENTRY_OPEN);
        mqtt.subscribe(TOPIC_EXIT_OPEN);
        mqtt.subscribe(TOPIC_STATUS);
        mqtt.subscribe(TOPIC_LCD_ENTRY);
        mqtt.subscribe(TOPIC_LCD_EXIT);
        mqtt.subscribe(TOPIC_LCD_ERROR);
        
        // Gửi heartbeat ngay khi kết nối
        sendHeartbeat();
        _lastHeartbeat = millis();
    } else {
        Serial.printf("failed, rc=%d\n", mqtt.state());
    }
}

void MQTTClientManager::loop() {
    // Kiểm tra MQTT
    if (!mqtt.connected()) {
        if (millis() - _lastReconnect > MQTT_RECONNECT_DELAY) {
            _lastReconnect = millis();
            _connect();
        }
        return;
    }
    
    mqtt.loop();
    
    // Gửi heartbeat
    if (millis() - _lastHeartbeat > HEARTBEAT_INTERVAL) {
        sendHeartbeat();
        _lastHeartbeat = millis();
    }
}

bool MQTTClientManager::isConnected() {
    return mqtt.connected();
}

void MQTTClientManager::sendHeartbeat() {
    if (!mqtt.connected()) return;
    
    StaticJsonDocument<256> doc;
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["uptime"] = millis() / 1000;
    doc["version"] = "v1.0.0";
    doc["mac"] = WiFi.macAddress();
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    mqtt.publish(TOPIC_HEARTBEAT, buffer);
}

void MQTTClientManager::sendEntryCard(const char* cardId) {
    if (!mqtt.connected()) return;
    
    StaticJsonDocument<128> doc;
    doc["card_id"] = cardId;
    doc["mac"] = WiFi.macAddress();
    doc["time"] = millis();
    
    char buffer[128];
    serializeJson(doc, buffer);
    
    mqtt.publish(TOPIC_ENTRY_CARD, buffer);
    Serial.printf("[MQTT] Entry card: %s\n", cardId);
}

void MQTTClientManager::sendExitCard(const char* cardId) {
    if (!mqtt.connected()) return;
    
    StaticJsonDocument<128> doc;
    doc["card_id"] = cardId;
    doc["mac"] = WiFi.macAddress();
    doc["time"] = millis();
    
    char buffer[128];
    serializeJson(doc, buffer);
    
    mqtt.publish(TOPIC_EXIT_CARD, buffer);
    Serial.printf("[MQTT] Exit card: %s\n", cardId);
}

void MQTTClientManager::sendSlotStatus(bool slots[], int count) {
    if (!mqtt.connected()) return;
    
    StaticJsonDocument<256> doc;
    JsonArray arr = doc.createNestedArray("slots");
    for (int i = 0; i < count; i++) {
        arr.add(slots[i]);
    }
    doc["occupied"] = 0;
    for (int i = 0; i < count; i++) {
        if (slots[i]) doc["occupied"] = (int)doc["occupied"] + 1;
    }
    doc["available"] = count - (int)doc["occupied"];
    doc["total"] = count;
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    mqtt.publish(TOPIC_SLOT_STATUS, buffer);
}

void MQTTClientManager::sendSlotChange(int slot, bool occupied) {
    if (!mqtt.connected()) return;
    
    StaticJsonDocument<128> doc;
    doc["slot"] = slot;
    doc["occupied"] = occupied;
    doc["time"] = millis();
    
    char buffer[128];
    serializeJson(doc, buffer);
    
    mqtt.publish(TOPIC_SLOT_CHANGE, buffer);
    Serial.printf("[MQTT] Slot %d: %s\n", slot, occupied ? "OCCUPIED" : "AVAILABLE");
}

void MQTTClientManager::setEntryOpenCallback(BarrierCallback callback) {
    _entryOpenCallback = callback;
}

void MQTTClientManager::setExitOpenCallback(BarrierCallback callback) {
    _exitOpenCallback = callback;
}

void MQTTClientManager::setLCDEntryCallback(LCDEntryCallback callback) {
    _lcdEntryCallback = callback;
}

void MQTTClientManager::setLCDExitCallback(LCDExitCallback callback) {
    _lcdExitCallback = callback;
}

void MQTTClientManager::setLCDErrorCallback(LCDErrorCallback callback) {
    _lcdErrorCallback = callback;
}

void MQTTClientManager::_staticCallback(char* topic, byte* payload, unsigned int length) {
    if (_instance) {
        _instance->_onMessage(topic, payload, length);
    }
}

void MQTTClientManager::_onMessage(char* topic, byte* payload, unsigned int length) {
    // Parse JSON
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    
    if (error) {
        Serial.printf("[MQTT] JSON error: %s\n", error.c_str());
        return;
    }
    
    Serial.printf("[MQTT] Received: %s\n", topic);
    
    // Xử lý theo topic
    if (strcmp(topic, TOPIC_ENTRY_OPEN) == 0) {
        Serial.println("[MQTT] -> Mở barrier VÀO");
        if (_entryOpenCallback) {
            _entryOpenCallback();
        }
    }
    else if (strcmp(topic, TOPIC_EXIT_OPEN) == 0) {
        Serial.println("[MQTT] -> Mở barrier RA");
        if (_exitOpenCallback) {
            _exitOpenCallback();
        }
    }
    else if (strcmp(topic, TOPIC_LCD_ENTRY) == 0) {
        // Hiển thị xe vào trên LCD
        const char* cardId = doc["card_id"] | "N/A";
        int slot = doc["slot"] | 0;
        Serial.printf("[MQTT] -> LCD Entry: %s, Slot %d\n", cardId, slot);
        if (_lcdEntryCallback) {
            _lcdEntryCallback(cardId, slot);
        }
    }
    else if (strcmp(topic, TOPIC_LCD_EXIT) == 0) {
        // Hiển thị xe ra trên LCD
        const char* cardId = doc["card_id"] | "N/A";
        int fee = doc["fee"] | 0;
        Serial.printf("[MQTT] -> LCD Exit: %s, Fee %d\n", cardId, fee);
        if (_lcdExitCallback) {
            _lcdExitCallback(cardId, fee);
        }
    }
    else if (strcmp(topic, TOPIC_LCD_ERROR) == 0) {
        // Hiển thị lỗi trên LCD
        const char* message = doc["message"] | "Loi he thong";
        Serial.printf("[MQTT] -> LCD Error: %s\n", message);
        if (_lcdErrorCallback) {
            _lcdErrorCallback(message);
        }
    }
}
