/*
 * MQTT Client - Kết nối với App Desktop
 * File: mqtt_client.h
 * Tham khảo từ baidoxe project
 */

#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==================== MQTT TOPICS ====================
#define TOPIC_ENTRY_CARD      "parking/entry/card"
#define TOPIC_EXIT_CARD       "parking/exit/card"
#define TOPIC_ENTRY_OPEN      "parking/entry/open"
#define TOPIC_EXIT_OPEN       "parking/exit/open"
#define TOPIC_STATUS          "parking/status"
#define TOPIC_HEARTBEAT       "parking/esp32/heartbeat"
#define TOPIC_SLOT_STATUS     "parking/slots/status"      // Trạng thái các slot
#define TOPIC_SLOT_CHANGE     "parking/slots/change"      // Khi slot thay đổi
#define TOPIC_LCD_ENTRY       "parking/lcd/entry"         // Hiển thị xe vào
#define TOPIC_LCD_EXIT        "parking/lcd/exit"          // Hiển thị xe ra
#define TOPIC_LCD_ERROR       "parking/lcd/error"         // Hiển thị lỗi

// ==================== CẤU HÌNH ====================
#define HEARTBEAT_INTERVAL    4000   // Gửi heartbeat mỗi 4 giây (giống baidoxe)
#define MQTT_RECONNECT_DELAY  2000   // Thử kết nối lại sau 2 giây

// ==================== CALLBACK TYPES ====================
typedef void (*BarrierCallback)();
typedef void (*LCDEntryCallback)(const char* cardId, int slot);
typedef void (*LCDExitCallback)(const char* cardId, int fee);
typedef void (*LCDErrorCallback)(const char* message);

// ==================== CLASS ====================
class MQTTClientManager {
public:
    MQTTClientManager();
    
    void begin(const char* server, int port);
    void loop();
    
    bool isConnected();
    
    // Gửi dữ liệu
    void sendEntryCard(const char* cardId);
    void sendExitCard(const char* cardId);
    void sendHeartbeat();
    void sendSlotStatus(bool slots[], int count);
    void sendSlotChange(int slot, bool occupied);
    
    // Callbacks
    void setEntryOpenCallback(BarrierCallback callback);
    void setExitOpenCallback(BarrierCallback callback);
    void setLCDEntryCallback(LCDEntryCallback callback);
    void setLCDExitCallback(LCDExitCallback callback);
    void setLCDErrorCallback(LCDErrorCallback callback);
    
private:
    char _server[64];
    int _port;
    
    unsigned long _lastHeartbeat;
    unsigned long _lastReconnect;
    
    BarrierCallback _entryOpenCallback;
    BarrierCallback _exitOpenCallback;
    LCDEntryCallback _lcdEntryCallback;
    LCDExitCallback _lcdExitCallback;
    LCDErrorCallback _lcdErrorCallback;
    
    void _connect();
    void _onMessage(char* topic, byte* payload, unsigned int length);
    
    static MQTTClientManager* _instance;
    static void _staticCallback(char* topic, byte* payload, unsigned int length);
};

#endif
