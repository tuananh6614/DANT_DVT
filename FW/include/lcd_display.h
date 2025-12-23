/*
 * LCD Display Manager - LCD 20x4 I2C
 * Hiển thị thông tin bãi xe
 */

#ifndef LCD_DISPLAY_H
#define LCD_DISPLAY_H

#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// LCD 20x4 I2C - Thử cả 2 địa chỉ phổ biến
#define LCD_COLS 20
#define LCD_ROWS 4

class LCDDisplayManager {
public:
    void begin();
    void loop();
    
    // Các màn hình hiển thị
    void showWelcome();
    void showIdle(int available, int total);
    void showEntry(const char* cardId, int slot);
    void showExit(const char* cardId, int fee);
    void showError(const char* message);
    void showConfigMode(const char* ssid, const char* ip);
    void showConnecting();
    void showConnected(const char* ip);
    
    // Cập nhật slot status
    void updateSlotStatus(bool* slots, int count);
    
    // Hiển thị message tạm thời
    void showMessage(const char* line1, const char* line2, const char* line3, const char* line4);
    
private:
    LiquidCrystal_I2C* lcd = nullptr;
    unsigned long messageEndTime = 0;
    bool showingMessage = false;
    bool lcdFound = false;
    
    // Slot status cache
    bool slotCache[10] = {false};
    int slotCount = 3;
    int availableSlots = 3;
    
    // Helper
    void centerPrint(int row, const char* text);
    void clearRow(int row);
    String formatMoney(int amount);
    bool scanI2C();
};

extern LCDDisplayManager lcdDisplay;

#endif
