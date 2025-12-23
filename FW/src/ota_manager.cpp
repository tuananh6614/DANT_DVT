/*
 * OTA Manager - Nạp code qua WiFi
 * File: ota_manager.cpp
 */

#include "../include/ota_manager.h"

// Static instance để dùng trong callback
static OTAManager* _instance = nullptr;

OTAManager::OTAManager() {
    _isUpdating = false;
    _displayCallback = nullptr;
    _instance = this;
}

void OTAManager::setDisplayCallback(OTADisplayCallback callback) {
    _displayCallback = callback;
}

void OTAManager::showStatus(const char* message, int progress) {
    Serial.printf("[OTA] %s", message);
    if (progress >= 0) {
        Serial.printf(" %d%%", progress);
    }
    Serial.println();
    
    if (_displayCallback) {
        _displayCallback(message, progress);
    }
}

bool OTAManager::isUpdating() {
    return _isUpdating;
}

void OTAManager::begin() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[OTA] WiFi chưa kết nối!");
        return;
    }
    
    Serial.println("[OTA] Đang khởi tạo...");
    
    // Khởi tạo mDNS
    if (MDNS.begin(OTA_HOSTNAME)) {
        Serial.printf("[OTA] mDNS: %s.local\n", OTA_HOSTNAME);
        MDNS.addService("arduino", "tcp", OTA_PORT);
    } else {
        Serial.println("[OTA] mDNS thất bại, vẫn có thể OTA qua IP");
    }
    
    // Cấu hình ArduinoOTA
    ArduinoOTA.setHostname(OTA_HOSTNAME);
    ArduinoOTA.setPassword(OTA_PASSWORD);
    ArduinoOTA.setPort(OTA_PORT);
    
    // Callback bắt đầu
    ArduinoOTA.onStart([this]() {
        _isUpdating = true;
        
        String type = (ArduinoOTA.getCommand() == U_FLASH) ? "Firmware" : "Filesystem";
        Serial.printf("[OTA] Bắt đầu cập nhật %s\n", type.c_str());
        
        showStatus("Đang cập nhật...", 0);
        
        // Tắt watchdog
        disableCore0WDT();
        disableCore1WDT();
    });
    
    // Callback progress
    ArduinoOTA.onProgress([this](unsigned int progress, unsigned int total) {
        int percent = (progress * 100) / total;
        
        static int lastPercent = -1;
        if (percent != lastPercent) {
            showStatus("Đang nạp", percent);
            lastPercent = percent;
        }
        
        // Feed watchdog
        esp_task_wdt_reset();
    });
    
    // Callback hoàn tất
    ArduinoOTA.onEnd([this]() {
        Serial.println("\n[OTA] Hoàn tất! Đang khởi động lại...");
        showStatus("Hoàn tất!", 100);
        
        enableCore0WDT();
        enableCore1WDT();
        
        _isUpdating = false;
        delay(1000);
    });
    
    // Callback lỗi
    ArduinoOTA.onError([this](ota_error_t error) {
        String errorMsg;
        
        switch (error) {
            case OTA_AUTH_ERROR:    errorMsg = "Sai mật khẩu"; break;
            case OTA_BEGIN_ERROR:   errorMsg = "Lỗi khởi tạo"; break;
            case OTA_CONNECT_ERROR: errorMsg = "Lỗi kết nối"; break;
            case OTA_RECEIVE_ERROR: errorMsg = "Lỗi nhận dữ liệu"; break;
            case OTA_END_ERROR:     errorMsg = "Lỗi kết thúc"; break;
            default:                errorMsg = "Lỗi không xác định"; break;
        }
        
        Serial.printf("[OTA] Lỗi: %s\n", errorMsg.c_str());
        showStatus(errorMsg.c_str(), -1);
        
        enableCore0WDT();
        enableCore1WDT();
        
        _isUpdating = false;
        delay(3000);
    });
    
    ArduinoOTA.begin();
    
    Serial.println("========================================");
    Serial.println("   OTA SẴN SÀNG");
    Serial.println("========================================");
    Serial.printf("   Hostname: %s\n", OTA_HOSTNAME);
    Serial.printf("   IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("   Port: %d\n", OTA_PORT);
    Serial.printf("   Password: %s\n", OTA_PASSWORD);
    Serial.printf("   Version: %s\n", CURRENT_VERSION);
    Serial.println("========================================");
    Serial.println("   Nạp code: pio run -t upload --upload-port <IP>");
    Serial.println("========================================\n");
}

void OTAManager::loop() {
    ArduinoOTA.handle();
}
