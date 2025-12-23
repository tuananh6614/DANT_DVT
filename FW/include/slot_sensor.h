/*
 * Slot Sensor - Cảm biến siêu âm phát hiện xe đỗ
 * File: slot_sensor.h
 */

#ifndef SLOT_SENSOR_H
#define SLOT_SENSOR_H

#include <Arduino.h>
#include <NewPing.h>

// Số lượng slot (cảm biến)
#define SLOT_COUNT 3
#define MAX_DISTANCE 200  // cm

// Ngưỡng phát hiện xe (cm) - dưới ngưỡng này = có xe
// Nếu cảm biến không kết nối, sẽ đọc 0 hoặc MAX_DISTANCE
#define DETECTION_THRESHOLD 5  // 5cm - có vật cản rất gần mới tính là có xe

// Cấu hình pins cho từng cảm biến
// CB1: Slot 1 - Trig 13, Echo 12
// CB2: Slot 2 - Trig 14, Echo 27
// CB3: Slot 3 - Trig 26, Echo 25

struct SlotConfig {
    uint8_t trigPin;
    uint8_t echoPin;
};

// Callback khi trạng thái slot thay đổi
typedef void (*SlotChangeCallback)(int slot, bool occupied);

class SlotSensorManager {
public:
    SlotSensorManager();
    
    void begin();
    void loop();
    
    // Lấy trạng thái
    bool isOccupied(int slot);           // slot 1-3
    int getDistance(int slot);           // Khoảng cách cm
    int getOccupiedCount();              // Số slot đã có xe
    int getAvailableCount();             // Số slot trống
    
    // Lấy trạng thái tất cả slots dạng JSON array [true, false, true]
    String getStatusJson();
    
    // Callback
    void setChangeCallback(SlotChangeCallback callback);
    
private:
    NewPing* _sensors[SLOT_COUNT];
    bool _occupied[SLOT_COUNT];
    int _distances[SLOT_COUNT];
    unsigned long _lastCheck;
    SlotChangeCallback _changeCallback;
    
    void _checkSlots();
};

#endif
