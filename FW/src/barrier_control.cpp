/*
 * Barrier Control - Servo + IR Sensor
 * Điều khiển barrier vào/ra với cảm biến hồng ngoại
 */

#include "../include/barrier_control.h"

BarrierControl barrierControl;

void BarrierControl::begin() {
    Serial.println("[Barrier] Initializing...");
    
    // Cấu hình chân IR sensor (input only, không cần pullup)
    pinMode(IR_ENTRY_PIN, INPUT);
    pinMode(IR_EXIT_PIN, INPUT);
    
    // Khởi tạo servo
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    
    servoEntry.setPeriodHertz(50);
    servoExit.setPeriodHertz(50);
    
    servoEntry.attach(SERVO_ENTRY_PIN, 500, 2400);
    servoExit.attach(SERVO_EXIT_PIN, 500, 2400);
    
    // Đóng barrier ban đầu
    servoEntry.write(SERVO_ENTRY_CLOSE_ANGLE);
    servoExit.write(SERVO_EXIT_CLOSE_ANGLE);
    
    delay(500);
    
    Serial.println("[Barrier] Ready!");
    Serial.printf("[Barrier] Entry Servo: GPIO%d (Open:%d, Close:%d)\n", 
        SERVO_ENTRY_PIN, SERVO_ENTRY_OPEN_ANGLE, SERVO_ENTRY_CLOSE_ANGLE);
    Serial.printf("[Barrier] Exit Servo: GPIO%d (Open:%d, Close:%d)\n", 
        SERVO_EXIT_PIN, SERVO_EXIT_OPEN_ANGLE, SERVO_EXIT_CLOSE_ANGLE);
    Serial.printf("[Barrier] Entry IR: GPIO%d, Exit IR: GPIO%d\n", IR_ENTRY_PIN, IR_EXIT_PIN);
}

void BarrierControl::loop() {
    unsigned long now = millis();
    
    // === XỬ LÝ BARRIER VÀO ===
    if (entryOpen) {
        bool irTriggered = isEntryIRTriggered();
        
        // QUAN TRỌNG: Nếu IR đang có vật cản -> KHÔNG ĐÓNG BARRIER
        if (irTriggered) {
            // Reset timeout khi có vật cản
            entryOpenTime = now;
            entryCarPassed = false;
        } else {
            // Không có vật cản
            // Nếu trước đó có vật cản -> xe đã đi qua
            if (entryIRLastState && !irTriggered) {
                if (now - entryIRLastChange > IR_DEBOUNCE_TIME) {
                    entryCarPassed = true;
                    Serial.println("[Barrier] Entry: Car passed, closing...");
                }
            }
            
            // Đóng barrier sau khi xe đi qua (và IR không còn vật cản)
            if (entryCarPassed) {
                delay(500);  // Chờ thêm để chắc chắn xe đi qua
                if (!isEntryIRTriggered()) {  // Kiểm tra lại lần nữa
                    closeEntry();
                }
                entryCarPassed = false;
            }
            // Timeout - chỉ đóng khi KHÔNG có vật cản
            else if (now - entryOpenTime > BARRIER_OPEN_TIME) {
                if (!isEntryIRTriggered()) {
                    Serial.println("[Barrier] Entry: Timeout, closing");
                    closeEntry();
                } else {
                    Serial.println("[Barrier] Entry: Timeout but obstacle detected, waiting...");
                    entryOpenTime = now;  // Reset timeout
                }
            }
        }
        
        // Cập nhật trạng thái IR
        if (irTriggered != entryIRLastState) {
            entryIRLastChange = now;
            entryIRLastState = irTriggered;
        }
    }
    
    // === XỬ LÝ BARRIER RA ===
    if (exitOpen) {
        bool irTriggered = isExitIRTriggered();
        
        // QUAN TRỌNG: Nếu IR đang có vật cản -> KHÔNG ĐÓNG BARRIER
        if (irTriggered) {
            // Reset timeout khi có vật cản
            exitOpenTime = now;
            exitCarPassed = false;
        } else {
            // Không có vật cản
            // Nếu trước đó có vật cản -> xe đã đi qua
            if (exitIRLastState && !irTriggered) {
                if (now - exitIRLastChange > IR_DEBOUNCE_TIME) {
                    exitCarPassed = true;
                    Serial.println("[Barrier] Exit: Car passed, closing...");
                }
            }
            
            // Đóng barrier sau khi xe đi qua (và IR không còn vật cản)
            if (exitCarPassed) {
                delay(500);  // Chờ thêm để chắc chắn xe đi qua
                if (!isExitIRTriggered()) {  // Kiểm tra lại lần nữa
                    closeExit();
                }
                exitCarPassed = false;
            }
            // Timeout - chỉ đóng khi KHÔNG có vật cản
            else if (now - exitOpenTime > BARRIER_OPEN_TIME) {
                if (!isExitIRTriggered()) {
                    Serial.println("[Barrier] Exit: Timeout, closing");
                    closeExit();
                } else {
                    Serial.println("[Barrier] Exit: Timeout but obstacle detected, waiting...");
                    exitOpenTime = now;  // Reset timeout
                }
            }
        }
        
        // Cập nhật trạng thái IR
        if (irTriggered != exitIRLastState) {
            exitIRLastChange = now;
            exitIRLastState = irTriggered;
        }
    }
}

void BarrierControl::openEntry() {
    if (!entryOpen) {
        Serial.printf("[Barrier] Opening ENTRY barrier -> %d degrees\n", SERVO_ENTRY_OPEN_ANGLE);
        servoEntry.write(SERVO_ENTRY_OPEN_ANGLE);
        entryOpen = true;
        entryOpenTime = millis();
        entryCarPassed = false;
        entryIRLastState = isEntryIRTriggered();
    }
}

void BarrierControl::openExit() {
    if (!exitOpen) {
        Serial.printf("[Barrier] Opening EXIT barrier -> %d degrees\n", SERVO_EXIT_OPEN_ANGLE);
        servoExit.write(SERVO_EXIT_OPEN_ANGLE);
        exitOpen = true;
        exitOpenTime = millis();
        exitCarPassed = false;
        exitIRLastState = isExitIRTriggered();
    }
}

void BarrierControl::closeEntry() {
    if (entryOpen) {
        Serial.printf("[Barrier] Closing ENTRY barrier -> %d degrees\n", SERVO_ENTRY_CLOSE_ANGLE);
        servoEntry.write(SERVO_ENTRY_CLOSE_ANGLE);
        entryOpen = false;
    }
}

void BarrierControl::closeExit() {
    if (exitOpen) {
        Serial.printf("[Barrier] Closing EXIT barrier -> %d degrees\n", SERVO_EXIT_CLOSE_ANGLE);
        servoExit.write(SERVO_EXIT_CLOSE_ANGLE);
        exitOpen = false;
    }
}

bool BarrierControl::isEntryIRTriggered() {
    // IR sensor thường LOW khi có vật cản, HIGH khi không có
    // Tùy loại sensor có thể đảo ngược
    return digitalRead(IR_ENTRY_PIN) == LOW;
}

bool BarrierControl::isExitIRTriggered() {
    return digitalRead(IR_EXIT_PIN) == LOW;
}
