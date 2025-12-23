/*
 * WiFi Manager - Tự phát WiFi để cấu hình
 * File: wifi_manager.h
 * 
 * Tính năng:
 * - Tự phát WiFi AP để cấu hình lần đầu
 * - mDNS: ESP32 tự quảng bá là "parking-esp32.local"
 * - Tự động tìm MQTT broker qua mDNS
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <EEPROM.h>
#include <ESPmDNS.h>

// ==================== CẤU HÌNH ====================
#define EEPROM_SIZE         512
#define WIFI_SSID_ADDR      0
#define WIFI_PASS_ADDR      64
#define MQTT_SERVER_ADDR    128
#define MQTT_PORT_ADDR      192

#define AP_SSID             "ParkingESP32_Setup"
#define AP_PASS             "12345678"

// ==================== mDNS ====================
// ESP32 sẽ có hostname: parking-esp32.local
// App Desktop sẽ quảng bá: parking-broker.local
#define MDNS_HOSTNAME       "parking-esp32"

// ==================== IP TĨNH ====================
// Đặt false nếu muốn dùng DHCP + mDNS (khuyến nghị)
#define USE_STATIC_IP       false
#define STATIC_IP           192, 168, 1, 88
#define STATIC_GATEWAY      192, 168, 1, 1
#define STATIC_SUBNET       255, 255, 255, 0
#define STATIC_DNS          8, 8, 8, 8

// ==================== CLASS ====================
class WiFiManager {
public:
    WiFiManager();
    
    void begin();
    void loop();
    
    bool isConfigMode();
    bool isConnected();
    
    String getSSID();
    String getPassword();
    String getMQTTServer();
    int getMQTTPort();
    
    void startConfigPortal();
    void resetConfig();
    
private:
    WebServer server;
    
    String _ssid;
    String _pass;
    String _mqttServer;
    int _mqttPort;
    
    bool _configMode;
    bool _connected;
    
    void loadConfig();
    void saveConfig();
    bool connectWiFi();
    
    // mDNS functions
    void startMDNS();
    String findMQTTBroker();
    
    void handleRoot();
    void handleSave();
    void handleReset();
    void handleScan();
    
    String getConfigPage();
    String scanNetworks();
};

#endif
