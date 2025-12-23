/*
 * WiFi Manager - Tự phát WiFi để cấu hình
 * File: wifi_manager.cpp
 */

#include "../include/wifi_manager.h"
#include <ESPmDNS.h>

WiFiManager::WiFiManager() : server(80) {
    _configMode = false;
    _connected = false;
    _mqttServer = "192.168.1.5";
    _mqttPort = 1883;
}

void WiFiManager::begin() {
    EEPROM.begin(EEPROM_SIZE);
    loadConfig();
    
    if (_ssid.length() == 0) {
        Serial.println("[WiFi] Chưa có cấu hình - Khởi động Config Portal");
        startConfigPortal();
    } else {
        Serial.println("[WiFi] Đang kết nối: " + _ssid);
        if (connectWiFi()) {
            _connected = true;
            Serial.println("[WiFi] Đã kết nối!");
            Serial.print("[WiFi] IP: ");
            Serial.println(WiFi.localIP());
        } else {
            Serial.println("[WiFi] Kết nối thất bại - Khởi động Config Portal");
            startConfigPortal();
        }
    }
}

void WiFiManager::loop() {
    if (_configMode) {
        server.handleClient();
    }
}

bool WiFiManager::isConfigMode() { return _configMode; }
bool WiFiManager::isConnected() { return _connected; }
String WiFiManager::getSSID() { return _ssid; }
String WiFiManager::getPassword() { return _pass; }
String WiFiManager::getMQTTServer() { return _mqttServer; }
int WiFiManager::getMQTTPort() { return _mqttPort; }

void WiFiManager::startConfigPortal() {
    _configMode = true;
    _connected = false;
    
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_SSID, AP_PASS);
    
    Serial.println("\n========================================");
    Serial.println("   CHẾ ĐỘ CẤU HÌNH WIFI");
    Serial.println("========================================");
    Serial.printf("   WiFi: %s\n", AP_SSID);
    Serial.printf("   Pass: %s\n", AP_PASS);
    Serial.printf("   IP:   %s\n", WiFi.softAPIP().toString().c_str());
    Serial.println("========================================\n");
    
    server.on("/", [this]() { handleRoot(); });
    server.on("/save", HTTP_POST, [this]() { handleSave(); });
    server.on("/reset", [this]() { handleReset(); });
    server.on("/scan", [this]() { handleScan(); });
    server.begin();
}

bool WiFiManager::connectWiFi() {
    WiFi.mode(WIFI_STA);
    
    // Cấu hình IP tĩnh
    #if USE_STATIC_IP
    IPAddress staticIP(STATIC_IP);
    IPAddress gateway(STATIC_GATEWAY);
    IPAddress subnet(STATIC_SUBNET);
    IPAddress dns(STATIC_DNS);
    
    if (!WiFi.config(staticIP, gateway, subnet, dns)) {
        Serial.println("[WiFi] Cấu hình IP tĩnh thất bại!");
    } else {
        Serial.printf("[WiFi] IP tĩnh: %s\n", staticIP.toString().c_str());
    }
    #endif
    
    WiFi.begin(_ssid.c_str(), _pass.c_str());
    
    int timeout = 20;
    while (WiFi.status() != WL_CONNECTED && timeout > 0) {
        delay(500);
        Serial.print(".");
        timeout--;
    }
    Serial.println();
    
    if (WiFi.status() == WL_CONNECTED) {
        // Khởi động mDNS
        startMDNS();
        
        // Thử tìm MQTT broker qua mDNS
        String foundBroker = findMQTTBroker();
        if (foundBroker.length() > 0 && foundBroker != _mqttServer) {
            Serial.printf("[WiFi] Auto-discovered MQTT: %s (saved: %s)\n", 
                foundBroker.c_str(), _mqttServer.c_str());
            // Ưu tiên dùng broker tìm được qua mDNS
            _mqttServer = foundBroker;
        }
    }
    
    return WiFi.status() == WL_CONNECTED;
}

// Khởi động mDNS để App có thể tìm ESP32 qua tên
void WiFiManager::startMDNS() {
    if (MDNS.begin("parking-esp32")) {
        // Đăng ký service để App có thể tìm
        MDNS.addService("parking", "tcp", 80);
        MDNS.addService("mqtt", "tcp", 1883);
        Serial.println("[mDNS] Started: parking-esp32.local");
    } else {
        Serial.println("[mDNS] Failed to start!");
    }
}

// Tìm MQTT broker qua mDNS (tên: parking-broker.local)
String WiFiManager::findMQTTBroker() {
    Serial.println("[mDNS] Searching for MQTT broker...");
    
    int n = MDNS.queryService("mqtt", "tcp");
    if (n > 0) {
        String brokerIP = MDNS.IP(0).toString();
        Serial.printf("[mDNS] Found broker: %s:%d\n", brokerIP.c_str(), MDNS.port(0));
        return brokerIP;
    }
    
    // Thử tìm theo hostname
    IPAddress brokerAddr;
    if (MDNS.queryHost("parking-broker", &brokerAddr, 3000)) {
        Serial.printf("[mDNS] Found broker by hostname: %s\n", brokerAddr.toString().c_str());
        return brokerAddr.toString();
    }
    
    Serial.println("[mDNS] Broker not found, using saved config");
    return "";
}


// ==================== EEPROM ====================
void WiFiManager::loadConfig() {
    char ssid[64], pass[64], mqtt[64];
    int port;
    
    EEPROM.get(WIFI_SSID_ADDR, ssid);
    EEPROM.get(WIFI_PASS_ADDR, pass);
    EEPROM.get(MQTT_SERVER_ADDR, mqtt);
    EEPROM.get(MQTT_PORT_ADDR, port);
    
    _ssid = String(ssid);
    _pass = String(pass);
    _mqttServer = String(mqtt);
    _mqttPort = port;
    
    // Validate
    if (_ssid == "ÿÿÿÿ" || _ssid.length() > 32) _ssid = "";
    if (_mqttServer.length() > 32 || _mqttServer.length() == 0) _mqttServer = "192.168.1.5";
    if (_mqttPort <= 0 || _mqttPort > 65535) _mqttPort = 1883;
    
    Serial.printf("[Config] SSID: %s\n", _ssid.c_str());
    Serial.printf("[Config] MQTT: %s:%d\n", _mqttServer.c_str(), _mqttPort);
}

void WiFiManager::saveConfig() {
    char ssid[64] = {0}, pass[64] = {0}, mqtt[64] = {0};
    
    _ssid.toCharArray(ssid, 64);
    _pass.toCharArray(pass, 64);
    _mqttServer.toCharArray(mqtt, 64);
    
    EEPROM.put(WIFI_SSID_ADDR, ssid);
    EEPROM.put(WIFI_PASS_ADDR, pass);
    EEPROM.put(MQTT_SERVER_ADDR, mqtt);
    EEPROM.put(MQTT_PORT_ADDR, _mqttPort);
    EEPROM.commit();
    
    Serial.println("[Config] Đã lưu cấu hình!");
}

void WiFiManager::resetConfig() {
    for (int i = 0; i < EEPROM_SIZE; i++) {
        EEPROM.write(i, 0);
    }
    EEPROM.commit();
    Serial.println("[Config] Đã reset cấu hình!");
}

// ==================== WEB HANDLERS ====================
void WiFiManager::handleRoot() {
    server.send(200, "text/html", getConfigPage());
}

void WiFiManager::handleSave() {
    if (server.hasArg("ssid") && server.hasArg("pass")) {
        _ssid = server.arg("ssid");
        _pass = server.arg("pass");
        if (server.hasArg("mqtt")) _mqttServer = server.arg("mqtt");
        if (server.hasArg("port")) _mqttPort = server.arg("port").toInt();
        
        saveConfig();
        
        String html = R"(
<!DOCTYPE html><html><head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>body{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;}
.card{background:#fff;padding:40px;border-radius:20px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.2);}
h2{color:#4CAF50;}p{color:#666;}</style>
</head><body><div class='card'>
<h2>✅ Đã lưu!</h2><p>ESP32 đang khởi động lại...</p>
</div></body></html>)";
        
        server.send(200, "text/html", html);
        delay(1500);
        ESP.restart();
    }
}

void WiFiManager::handleReset() {
    resetConfig();
    String html = R"(
<!DOCTYPE html><html><head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>body{font-family:Arial;background:#f44336;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;}
.card{background:#fff;padding:40px;border-radius:20px;text-align:center;}</style>
</head><body><div class='card'>
<h2>🔄 Đã reset!</h2><p>ESP32 đang khởi động lại...</p>
</div></body></html>)";
    
    server.send(200, "text/html", html);
    delay(1500);
    ESP.restart();
}

void WiFiManager::handleScan() {
    server.send(200, "application/json", scanNetworks());
}

String WiFiManager::scanNetworks() {
    int n = WiFi.scanNetworks();
    String json = "[";
    for (int i = 0; i < n; i++) {
        if (i > 0) json += ",";
        json += "{\"ssid\":\"" + WiFi.SSID(i) + "\",\"rssi\":" + String(WiFi.RSSI(i)) + "}";
    }
    json += "]";
    return json;
}


// ==================== CONFIG PAGE ====================
String WiFiManager::getConfigPage() {
    return R"(
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>Cấu hình ESP32</title>
    <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px;display:flex;align-items:center;justify-content:center}
        .card{background:#fff;padding:30px;border-radius:20px;box-shadow:0 15px 50px rgba(0,0,0,0.3);width:100%;max-width:380px}
        .logo{text-align:center;font-size:50px;margin-bottom:10px}
        h1{text-align:center;color:#333;font-size:20px;margin-bottom:5px}
        .sub{text-align:center;color:#888;font-size:13px;margin-bottom:25px}
        .section{background:#f8f9fa;padding:15px;border-radius:12px;margin-bottom:15px}
        .section-title{color:#667eea;font-size:12px;font-weight:700;margin-bottom:12px;text-transform:uppercase}
        .form-group{margin-bottom:12px}
        label{display:block;color:#555;font-size:13px;margin-bottom:5px}
        input,select{width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:10px;font-size:15px}
        input:focus,select:focus{outline:none;border-color:#667eea}
        .wifi-list{max-height:150px;overflow-y:auto;margin-bottom:10px}
        .wifi-item{padding:10px;background:#fff;border:1px solid #eee;border-radius:8px;margin-bottom:5px;cursor:pointer;display:flex;justify-content:space-between}
        .wifi-item:hover{background:#f0f0ff;border-color:#667eea}
        .signal{color:#888;font-size:12px}
        button{width:100%;padding:14px;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;margin-top:10px}
        .btn-save{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
        .btn-save:hover{opacity:0.9}
        .btn-scan{background:#4CAF50;color:#fff}
        .btn-reset{background:#f5f5f5;color:#666}
        .info{background:#e3f2fd;padding:12px;border-radius:10px;font-size:12px;color:#1565c0;margin-top:15px}
        .loading{display:none;text-align:center;padding:20px}
    </style>
</head>
<body>
    <div class='card'>
        <div class='logo'>🅿️</div>
        <h1>Cấu hình ESP32</h1>
        <p class='sub'>Hệ thống quản lý bãi xe</p>
        
        <form action='/save' method='POST'>
            <div class='section'>
                <div class='section-title'>📶 WiFi</div>
                <button type='button' class='btn-scan' onclick='scanWifi()'>🔍 Quét WiFi</button>
                <div id='wifi-list' class='wifi-list'></div>
                <div class='loading' id='loading'>Đang quét...</div>
                <div class='form-group'>
                    <label>Tên WiFi</label>
                    <input type='text' name='ssid' id='ssid' placeholder='Chọn hoặc nhập WiFi' required>
                </div>
                <div class='form-group'>
                    <label>Mật khẩu</label>
                    <input type='password' name='pass' placeholder='Nhập mật khẩu WiFi' required>
                </div>
            </div>
            
            <div class='section'>
                <div class='section-title'>📡 MQTT Server</div>
                <div class='form-group'>
                    <label>IP Server (hoặc để trống để tự tìm)</label>
                    <input type='text' name='mqtt' value='' placeholder='parking-broker.local hoặc IP'>
                </div>
                <div class='form-group'>
                    <label>Port</label>
                    <input type='number' name='port' value='1883'>
                </div>
                <p style='color:#888;font-size:11px;margin-top:5px;'>
                    Tip: Để trống IP, ESP32 sẽ tự tìm broker qua mDNS
                </p>
            </div>
            
            <button type='submit' class='btn-save'>💾 Lưu & Kết nối</button>
        </form>
        
        <button class='btn-reset' onclick="location.href='/reset'">🔄 Reset cấu hình</button>
        
        <div class='info'>
            <strong>💡 Hướng dẫn:</strong><br>
            1. Quét và chọn WiFi<br>
            2. Nhập IP máy tính chạy App<br>
            3. Nhấn "Lưu & Kết nối"
        </div>
    </div>
    
    <script>
        function scanWifi(){
            document.getElementById('loading').style.display='block';
            document.getElementById('wifi-list').innerHTML='';
            fetch('/scan').then(r=>r.json()).then(data=>{
                document.getElementById('loading').style.display='none';
                let html='';
                data.forEach(w=>{
                    let signal=w.rssi>-50?'📶📶📶':w.rssi>-70?'📶📶':'📶';
                    html+="<div class='wifi-item' onclick=\"document.getElementById('ssid').value='"+w.ssid+"'\">"+
                        "<span>"+w.ssid+"</span><span class='signal'>"+signal+" "+w.rssi+"dBm</span></div>";
                });
                document.getElementById('wifi-list').innerHTML=html||'<p>Không tìm thấy WiFi</p>';
            });
        }
        scanWifi();
    </script>
</body>
</html>
)";
}
