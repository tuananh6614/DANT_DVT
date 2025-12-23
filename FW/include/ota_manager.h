/*
 * OTA Manager - Nạp code qua WiFi
 * File: ota_manager.h
 */

#ifndef OTA_MANAGER_H
#define OTA_MANAGER_H

#include <Arduino.h>
#include <ArduinoOTA.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <esp_task_wdt.h>

// ==================== CẤU HÌNH OTA ====================
#define OTA_HOSTNAME    "ESP32-Parking"
#define OTA_PASSWORD    "parking123"
#define OTA_PORT        3232
#define CURRENT_VERSION "v1.0.0"

// ==================== CALLBACK TYPES ====================
typedef void (*OTADisplayCallback)(const char* message, int progress);

// ==================== CLASS ====================
class OTAManager {
public:
    OTAManager();
    
    void begin();
    void loop();
    
    bool isUpdating();
    
    // Set callback để hiển thị trạng thái OTA (nếu có màn hình)
    void setDisplayCallback(OTADisplayCallback callback);
    
private:
    bool _isUpdating;
    OTADisplayCallback _displayCallback;
    
    void showStatus(const char* message, int progress = -1);
};

#endif
