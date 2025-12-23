/*
 * LCD Display Manager - LCD 20x4 I2C
 */

#include "../include/lcd_display.h"

LCDDisplayManager lcdDisplay;

bool LCDDisplayManager::scanI2C() {
    // Quét tìm địa chỉ LCD I2C
    uint8_t addresses[] = {0x27, 0x3F, 0x20, 0x38};
    
    for (int i = 0; i < 4; i++) {
        Wire.beginTransmission(addresses[i]);
        if (Wire.endTransmission() == 0) {
            Serial.printf("[LCD] Found at 0x%02X\n", addresses[i]);
            lcd = new LiquidCrystal_I2C(addresses[i], LCD_COLS, LCD_ROWS);
            return true;
        }
    }
    Serial.println("[LCD] Not found!");
    return false;
}

void LCDDisplayManager::begin() {
    // Khởi tạo I2C với chân mặc định ESP32
    Wire.begin(21, 22);
    delay(100);
    
    // Quét tìm LCD
    if (!scanI2C()) {
        lcdFound = false;
        return;
    }
    
    lcdFound = true;
    lcd->init();
    lcd->backlight();
    lcd->clear();
    
    Serial.println("[LCD] Initialized OK");
    showWelcome();
}

void LCDDisplayManager::loop() {
    if (!lcdFound) return;
    
    // Hết thời gian message -> quay về idle
    if (showingMessage && millis() > messageEndTime) {
        showingMessage = false;
        showIdle(availableSlots, slotCount);
    }
}

void LCDDisplayManager::showWelcome() {
    if (!lcdFound) return;
    
    lcd->clear();
    centerPrint(0, "********************");
    centerPrint(1, "BAI XE THONG MINH");
    centerPrint(2, "SMART PARKING");
    centerPrint(3, "********************");
}

void LCDDisplayManager::showIdle(int available, int total) {
    if (!lcdFound) return;
    
    availableSlots = available;
    slotCount = total;
    showingMessage = false;
    
    lcd->clear();
    
    // Dòng 1: Tiêu đề
    centerPrint(0, "BAI XE THONG MINH");
    
    // Dòng 2: Số chỗ trống
    char line[21];
    snprintf(line, 21, "Cho trong: %d/%d", available, total);
    centerPrint(1, line);
    
    // Dòng 3: Trạng thái slot
    lcd->setCursor(0, 2);
    lcd->print("Slot: ");
    for (int i = 0; i < slotCount && i < 10; i++) {
        lcd->print(slotCache[i] ? "X" : "O");
    }
    
    // Dòng 4: Hướng dẫn
    centerPrint(3, "Vui long quet the...");
}

void LCDDisplayManager::showEntry(const char* cardId, int slot) {
    if (!lcdFound) return;
    
    lcd->clear();
    
    centerPrint(0, "=== XE VAO ===");
    
    // Dòng 2: Mã thẻ (cắt ngắn nếu dài)
    char line[21];
    snprintf(line, 21, "The: %.14s", cardId);
    lcd->setCursor(0, 1);
    lcd->print(line);
    
    // Dòng 3: Slot
    snprintf(line, 21, "Vi tri: Slot %d", slot);
    lcd->setCursor(0, 2);
    lcd->print(line);
    
    // Dòng 4
    centerPrint(3, "Chuc quy khach vui!");
    
    messageEndTime = millis() + 4000;
    showingMessage = true;
}

void LCDDisplayManager::showExit(const char* cardId, int fee) {
    if (!lcdFound) return;
    
    lcd->clear();
    
    centerPrint(0, "=== XE RA ===");
    
    // Dòng 2: Mã thẻ
    char line[21];
    snprintf(line, 21, "The: %.14s", cardId);
    lcd->setCursor(0, 1);
    lcd->print(line);
    
    // Dòng 3: Phí
    String money = formatMoney(fee);
    snprintf(line, 21, "Phi: %s VND", money.c_str());
    lcd->setCursor(0, 2);
    lcd->print(line);
    
    // Dòng 4
    centerPrint(3, "Cam on, hen gap lai!");
    
    messageEndTime = millis() + 4000;
    showingMessage = true;
}

void LCDDisplayManager::showError(const char* message) {
    if (!lcdFound) return;
    
    lcd->clear();
    
    centerPrint(0, "!!! LOI !!!");
    centerPrint(1, "");
    
    // Cắt message nếu dài quá 20 ký tự
    char line[21];
    strncpy(line, message, 20);
    line[20] = '\0';
    centerPrint(2, line);
    
    centerPrint(3, "");
    
    messageEndTime = millis() + 3000;
    showingMessage = true;
}

void LCDDisplayManager::showConfigMode(const char* ssid, const char* ip) {
    if (!lcdFound) return;
    
    lcd->clear();
    
    centerPrint(0, "CAU HINH WIFI");
    
    char line[21];
    snprintf(line, 21, "WiFi: %.13s", ssid);
    lcd->setCursor(0, 1);
    lcd->print(line);
    
    snprintf(line, 21, "IP: %s", ip);
    lcd->setCursor(0, 2);
    lcd->print(line);
    
    centerPrint(3, "Ket noi de cau hinh");
}

void LCDDisplayManager::showConnecting() {
    if (!lcdFound) return;
    
    lcd->clear();
    centerPrint(0, "");
    centerPrint(1, "DANG KET NOI...");
    centerPrint(2, "Vui long cho...");
    centerPrint(3, "");
}

void LCDDisplayManager::showConnected(const char* ip) {
    if (!lcdFound) return;
    
    lcd->clear();
    centerPrint(0, "");
    centerPrint(1, "DA KET NOI!");
    
    char line[21];
    snprintf(line, 21, "IP: %s", ip);
    centerPrint(2, line);
    centerPrint(3, "");
}

void LCDDisplayManager::updateSlotStatus(bool* slots, int count) {
    slotCount = count;
    availableSlots = 0;
    
    for (int i = 0; i < count && i < 10; i++) {
        slotCache[i] = slots[i];
        if (!slots[i]) availableSlots++;
    }
    
    // Nếu không đang hiển thị message, refresh màn hình idle
    if (!showingMessage && lcdFound && lcd) {
        // Cập nhật dòng 2: Số chỗ trống
        char line[21];
        snprintf(line, 21, "Cho trong: %d/%d  ", availableSlots, slotCount);
        lcd->setCursor(0, 1);
        lcd->print(line);
        
        // Cập nhật dòng 3: Trạng thái slot
        lcd->setCursor(0, 2);
        lcd->print("Slot: ");
        for (int i = 0; i < slotCount && i < 10; i++) {
            lcd->print(slotCache[i] ? "X" : "O");
        }
        // Padding
        for (int i = slotCount; i < 14; i++) {
            lcd->print(" ");
        }
    }
}

void LCDDisplayManager::showMessage(const char* line1, const char* line2, const char* line3, const char* line4) {
    if (!lcdFound) return;
    
    lcd->clear();
    if (strlen(line1) > 0) centerPrint(0, line1);
    if (strlen(line2) > 0) centerPrint(1, line2);
    if (strlen(line3) > 0) centerPrint(2, line3);
    if (strlen(line4) > 0) centerPrint(3, line4);
    
    messageEndTime = millis() + 3000;
    showingMessage = true;
}

// ============ Helper ============

void LCDDisplayManager::centerPrint(int row, const char* text) {
    if (!lcdFound || !lcd) return;
    
    int len = strlen(text);
    int pos = (LCD_COLS - len) / 2;
    if (pos < 0) pos = 0;
    
    clearRow(row);
    lcd->setCursor(pos, row);
    lcd->print(text);
}

void LCDDisplayManager::clearRow(int row) {
    if (!lcdFound || !lcd) return;
    
    lcd->setCursor(0, row);
    lcd->print("                    ");  // 20 spaces
}

String LCDDisplayManager::formatMoney(int amount) {
    if (amount < 1000) return String(amount);
    
    String result = "";
    String num = String(amount);
    int len = num.length();
    
    for (int i = 0; i < len; i++) {
        if (i > 0 && (len - i) % 3 == 0) {
            result += ",";
        }
        result += num[i];
    }
    return result;
}
