/*
 * Slot Sensor - Cảm biến siêu âm phát hiện xe đỗ
 * File: slot_sensor.cpp
 */

#include "../include/slot_sensor.h"

// Cấu hình pins theo yêu cầu
static const SlotConfig slotConfigs[SLOT_COUNT] = {
    {13, 12},  // Slot 1: Trig 13, Echo 12
    {14, 27},  // Slot 2: Trig 14, Echo 27
    {26, 25}   // Slot 3: Trig 26, Echo 25
};

SlotSensorManager::SlotSensorManager() {
    _lastCheck = 0;
    _changeCallback = nullptr;
    
    for (int i = 0; i < SLOT_COUNT; i++) {
        _sensors[i] = nullptr;
        _occupied[i] = false;
        _distances[i] = MAX_DISTANCE;
    }
}

void SlotSensorManager::begin() {
    Serial.println("[SLOT] Initializing ultrasonic sensors...");
    
    for (int i = 0; i < SLOT_COUNT; i++) {
        _sensors[i] = new NewPing(
            slotConfigs[i].trigPin,
            slotConfigs[i].echoPin,
            MAX_DISTANCE
        );
        Serial.printf("[SLOT] Slot %d: Trig=%d, Echo=%d\n", 
            i + 1, slotConfigs[i].trigPin, slotConfigs[i].echoPin);
    }
    
    // Đọc trạng thái ban đầu
    delay(100);
    _checkSlots();
    
    Serial.printf("[SLOT] Ready! Occupied: %d/%d\n", getOccupiedCount(), SLOT_COUNT);
}

void SlotSensorManager::loop() {
    // Kiểm tra mỗi 500ms
    if (millis() - _lastCheck >= 500) {
        _checkSlots();
        _lastCheck = millis();
    }
}

void SlotSensorManager::_checkSlots() {
    for (int i = 0; i < SLOT_COUNT; i++) {
        // Đọc khoảng cách (median của 5 lần đo)
        unsigned int distance = _sensors[i]->ping_median(5);
        distance = distance / US_ROUNDTRIP_CM;
        
        // Nếu không đọc được (0), giữ nguyên giá trị cũ
        if (distance == 0) {
            distance = MAX_DISTANCE;
        }
        
        _distances[i] = distance;
        
        // Xác định có xe hay không
        bool newOccupied = (distance < DETECTION_THRESHOLD);
        
        // Nếu trạng thái thay đổi
        if (newOccupied != _occupied[i]) {
            _occupied[i] = newOccupied;
            
            Serial.printf("[SLOT] Slot %d: %s (distance: %d cm)\n",
                i + 1,
                newOccupied ? "OCCUPIED" : "AVAILABLE",
                distance
            );
            
            // Gọi callback
            if (_changeCallback) {
                _changeCallback(i + 1, newOccupied);
            }
        }
    }
}

bool SlotSensorManager::isOccupied(int slot) {
    if (slot < 1 || slot > SLOT_COUNT) return false;
    return _occupied[slot - 1];
}

int SlotSensorManager::getDistance(int slot) {
    if (slot < 1 || slot > SLOT_COUNT) return -1;
    return _distances[slot - 1];
}

int SlotSensorManager::getOccupiedCount() {
    int count = 0;
    for (int i = 0; i < SLOT_COUNT; i++) {
        if (_occupied[i]) count++;
    }
    return count;
}

int SlotSensorManager::getAvailableCount() {
    return SLOT_COUNT - getOccupiedCount();
}

String SlotSensorManager::getStatusJson() {
    String json = "[";
    for (int i = 0; i < SLOT_COUNT; i++) {
        if (i > 0) json += ",";
        json += _occupied[i] ? "true" : "false";
    }
    json += "]";
    return json;
}

void SlotSensorManager::setChangeCallback(SlotChangeCallback callback) {
    _changeCallback = callback;
}
