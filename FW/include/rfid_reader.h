/*
 * RFID Reader - Đọc thẻ RFID cho xe vào/ra
 * File: rfid_reader.h
 * 
 * Cấu hình:
 * - RFID 1 (Xe vào): RST=2, SS=4
 * - RFID 2 (Xe ra): RST=17, SS=5
 * - SPI: MOSI=23, MISO=19, SCK=18
 */

#ifndef RFID_READER_H
#define RFID_READER_H

#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>

// Pin configuration
#define RFID_MOSI 23
#define RFID_MISO 19
#define RFID_SCK  18

// RFID 1 - Xe vào (Entry)
#define RFID1_RST 17
#define RFID1_SS  5

// RFID 2 - Xe ra (Exit)
#define RFID2_RST 2
#define RFID2_SS  4

// Debounce time (ms) - tránh đọc trùng thẻ
#define RFID_DEBOUNCE_TIME 3000

// Callback types
typedef void (*RFIDCallback)(const char* cardId);

class RFIDReaderManager {
public:
    RFIDReaderManager();
    
    void begin();
    void loop();
    
    // Callbacks
    void setEntryCallback(RFIDCallback callback);
    void setExitCallback(RFIDCallback callback);
    
private:
    MFRC522* _rfid1;  // Entry
    MFRC522* _rfid2;  // Exit
    
    String _lastCard1;
    String _lastCard2;
    unsigned long _lastRead1;
    unsigned long _lastRead2;
    unsigned long _lastReset;  // Thời điểm reset cuối
    
    RFIDCallback _entryCallback;
    RFIDCallback _exitCallback;
    
    String _readCard(MFRC522* rfid);
    bool _isDebounced(const String& cardId, String& lastCard, unsigned long& lastRead);
    void _softReset();  // Soft reset RFID readers
};

#endif
