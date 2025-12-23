/*
 * HỆ THỐNG QUẢN LÝ BÃI XE - ESP32 FIRMWARE
 * File: main.cpp
 * 
 * Tính năng:
 * - WiFi Manager: Tự phát WiFi để cấu hình
 * - OTA: Nạp code qua WiFi
 * - MQTT: Kết nối với App Desktop
 * - Cảm biến siêu âm: Phát hiện xe đỗ
 * - RFID: Quẹt thẻ xe vào/ra
 * - LCD 20x4: Hiển thị thông tin
 */

#include <Arduino.h>
#include "../include/wifi_manager.h"
#include "../include/ota_manager.h"
#include "../include/mqtt_client.h"
#include "../include/slot_sensor.h"
#include "../include/rfid_reader.h"
#include "../include/lcd_display.h"
#include "../include/barrier_control.h"

// LED để hiển thị trạng thái
#define LED_PIN 2

WiFiManager wifiManager;
OTAManager otaManager;
MQTTClientManager mqttClient;
SlotSensorManager slotSensor;
RFIDReaderManager rfidReader;

// Biến lưu trạng thái slot để gửi MQTT
bool slotStatus[SLOT_COUNT] = {false};
unsigned long lastSlotUpdate = 0;

// Callback hiển thị trạng thái OTA qua LED và LCD
void otaDisplayCallback(const char* message, int progress) {
    if (progress >= 0) {
        // Nhấp nháy LED theo progress
        digitalWrite(LED_PIN, (progress / 10) % 2);
        
        // Hiển thị trên LCD
        char line2[21];
        snprintf(line2, 21, "Tien trinh: %d%%", progress);
        lcdDisplay.showMessage("DANG CAP NHAT...", line2, "", "Vui long cho...");
    }
}

// Callback mở barrier vào
void onEntryOpen() {
    Serial.println("[Main] Mở barrier VÀO");
    barrierControl.openEntry();
}

// Callback mở barrier ra
void onExitOpen() {
    Serial.println("[Main] Mở barrier RA");
    barrierControl.openExit();
}

// Callback hiển thị xe vào trên LCD
void onLCDEntry(const char* cardId, int slot) {
    lcdDisplay.showEntry(cardId, slot);
}

// Callback hiển thị xe ra trên LCD
void onLCDExit(const char* cardId, int fee) {
    lcdDisplay.showExit(cardId, fee);
}

// Callback hiển thị lỗi trên LCD
void onLCDError(const char* message) {
    lcdDisplay.showError(message);
}

// Callback khi slot thay đổi trạng thái
void onSlotChange(int slot, bool occupied) {
    // Cập nhật trạng thái
    slotStatus[slot - 1] = occupied;
    
    // Cập nhật LCD
    lcdDisplay.updateSlotStatus(slotStatus, SLOT_COUNT);
    
    // Gửi thông báo thay đổi qua MQTT
    if (mqttClient.isConnected()) {
        mqttClient.sendSlotChange(slot, occupied);
        mqttClient.sendSlotStatus(slotStatus, SLOT_COUNT);
    }
}

// Callback khi quẹt thẻ xe vào
void onEntryCard(const char* cardId) {
    Serial.printf("[Main] Entry card: %s\n", cardId);
    
    // Hiển thị trên LCD - chờ phản hồi từ App
    lcdDisplay.showMessage("DANG XU LY...", "", cardId, "Vui long cho...");
    
    if (mqttClient.isConnected()) {
        mqttClient.sendEntryCard(cardId);
    }
}

// Callback khi quẹt thẻ xe ra
void onExitCard(const char* cardId) {
    Serial.printf("[Main] Exit card: %s\n", cardId);
    
    // Hiển thị trên LCD - chờ phản hồi từ App
    lcdDisplay.showMessage("DANG XU LY...", "", cardId, "Vui long cho...");
    
    if (mqttClient.isConnected()) {
        mqttClient.sendExitCard(cardId);
    }
}

// Tính số slot trống
int countAvailableSlots() {
    int count = 0;
    for (int i = 0; i < SLOT_COUNT; i++) {
        if (!slotStatus[i]) count++;
    }
    return count;
}

void setup() {
    Serial.begin(115200);
    Serial.println("\n\n========================================");
    Serial.println("   HỆ THỐNG QUẢN LÝ BÃI XE");
    Serial.println("========================================\n");
    
    pinMode(LED_PIN, OUTPUT);
    
    // Khởi động LCD
    lcdDisplay.begin();
    
    // Khởi động WiFi Manager
    lcdDisplay.showConnecting();
    wifiManager.begin();
    
    // Kiểm tra chế độ cấu hình
    if (wifiManager.isConfigMode()) {
        lcdDisplay.showConfigMode("ParkingESP32_Setup", "192.168.4.1");
    }
    // Nếu đã kết nối WiFi, khởi động các module khác
    else if (wifiManager.isConnected()) {
        Serial.println("[Main] WiFi đã kết nối!");
        Serial.printf("[Main] MQTT Server: %s:%d\n", 
            wifiManager.getMQTTServer().c_str(), 
            wifiManager.getMQTTPort());
        
        // Hiển thị IP
        lcdDisplay.showConnected(WiFi.localIP().toString().c_str());
        
        // Khởi động OTA
        otaManager.setDisplayCallback(otaDisplayCallback);
        otaManager.begin();
        
        // Khởi động MQTT
        mqttClient.setEntryOpenCallback(onEntryOpen);
        mqttClient.setExitOpenCallback(onExitOpen);
        mqttClient.setLCDEntryCallback(onLCDEntry);
        mqttClient.setLCDExitCallback(onLCDExit);
        mqttClient.setLCDErrorCallback(onLCDError);
        mqttClient.begin(wifiManager.getMQTTServer().c_str(), wifiManager.getMQTTPort());
        
        // Khởi động cảm biến slot
        slotSensor.setChangeCallback(onSlotChange);
        slotSensor.begin();
        
        // Khởi động RFID
        rfidReader.setEntryCallback(onEntryCard);
        rfidReader.setExitCallback(onExitCard);
        rfidReader.begin();
        
        // Khởi động Barrier Control (Servo + IR)
        barrierControl.begin();
        
        // Cập nhật trạng thái ban đầu
        for (int i = 0; i < SLOT_COUNT; i++) {
            slotStatus[i] = slotSensor.isOccupied(i + 1);
        }
        
        // Hiển thị màn hình chính
        lcdDisplay.updateSlotStatus(slotStatus, SLOT_COUNT);
        lcdDisplay.showIdle(countAvailableSlots(), SLOT_COUNT);
        
        digitalWrite(LED_PIN, HIGH);
    }
}

void loop() {
    // Xử lý WiFi Manager (config portal)
    wifiManager.loop();
    
    // Xử lý LCD
    lcdDisplay.loop();
    
    // Xử lý OTA
    if (wifiManager.isConnected()) {
        otaManager.loop();
    }
    
    // Nếu đang OTA, không làm gì khác
    if (otaManager.isUpdating()) {
        return;
    }
    
    if (wifiManager.isConfigMode()) {
        // Nhấp nháy LED khi đang ở chế độ cấu hình
        static unsigned long lastBlink = 0;
        if (millis() - lastBlink > 300) {
            digitalWrite(LED_PIN, !digitalRead(LED_PIN));
            lastBlink = millis();
        }
    } else if (wifiManager.isConnected()) {
        // Xử lý MQTT
        mqttClient.loop();
        
        // Xử lý cảm biến slot
        slotSensor.loop();
        
        // Xử lý RFID
        rfidReader.loop();
        
        // Xử lý Barrier (servo + IR sensor)
        barrierControl.loop();
        
        // Gửi trạng thái slot định kỳ (mỗi 10 giây)
        if (millis() - lastSlotUpdate > 10000) {
            if (mqttClient.isConnected()) {
                mqttClient.sendSlotStatus(slotStatus, SLOT_COUNT);
            }
            lastSlotUpdate = millis();
        }
    }
    
    delay(50);
}
