/*
 * Barrier Control - Servo + IR Sensor
 * Điều khiển barrier vào/ra với cảm biến hồng ngoại
 * 
 * Chân kết nối:
 * - Servo VÀO: GPIO 32
 * - Servo RA: GPIO 33
 * - IR Sensor VÀO: GPIO 34 (input only)
 * - IR Sensor RA: GPIO 35 (input only)
 */

#ifndef BARRIER_CONTROL_H
#define BARRIER_CONTROL_H

#include <Arduino.h>
#include <ESP32Servo.h>

// Chân servo
#define SERVO_ENTRY_PIN 33
#define SERVO_EXIT_PIN 32

// Chân cảm biến hồng ngoại (input only pins)
#define IR_ENTRY_PIN 35

#define IR_EXIT_PIN 34

// Góc servo - Điều chỉnh theo cách lắp đặt thực tế
// Servo VÀO
#define SERVO_ENTRY_OPEN_ANGLE 90     // Góc mở barrier vào (gạt lên)
#define SERVO_ENTRY_CLOSE_ANGLE 0     // Góc đóng barrier vào (gạt xuống)

// Servo RA  
#define SERVO_EXIT_OPEN_ANGLE 90      // Góc mở barrier ra (gạt lên)
#define SERVO_EXIT_CLOSE_ANGLE 0      // Góc đóng barrier ra (gạt xuống)

// Thời gian
#define BARRIER_OPEN_TIME 5000  // Thời gian mở tối đa (ms) nếu không có xe đi qua
#define IR_DEBOUNCE_TIME 200    // Debounce cho IR sensor (ms)

class BarrierControl {
public:
    void begin();
    void loop();
    
    // Mở barrier
    void openEntry();
    void openExit();
    
    // Đóng barrier (thường tự động sau khi xe đi qua)
    void closeEntry();
    void closeExit();
    
    // Trạng thái
    bool isEntryOpen() { return entryOpen; }
    bool isExitOpen() { return exitOpen; }
    bool isEntryIRTriggered();  // Xe đang ở cảm biến vào
    bool isExitIRTriggered();   // Xe đang ở cảm biến ra
    
private:
    Servo servoEntry;
    Servo servoExit;
    
    bool entryOpen = false;
    bool exitOpen = false;
    
    unsigned long entryOpenTime = 0;
    unsigned long exitOpenTime = 0;
    
    // Trạng thái IR để phát hiện xe đi qua
    bool entryIRLastState = false;
    bool exitIRLastState = false;
    unsigned long entryIRLastChange = 0;
    unsigned long exitIRLastChange = 0;
    
    // Cờ đánh dấu xe đã đi qua
    bool entryCarPassed = false;
    bool exitCarPassed = false;
};

extern BarrierControl barrierControl;

#endif
