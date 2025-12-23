/*
 * RFID Reader - Đọc thẻ RFID cho xe vào/ra
 * File: rfid_reader.cpp
 * 
 * Fix: Thêm soft reset định kỳ để tránh RFID bị treo
 */

#include "../include/rfid_reader.h"

// Reset RFID mỗi 30 giây để tránh bị treo
#define RFID_RESET_INTERVAL 30000

RFIDReaderManager::RFIDReaderManager() {
    _rfid1 = nullptr;
    _rfid2 = nullptr;
    _lastCard1 = "";
    _lastCard2 = "";
    _lastRead1 = 0;
    _lastRead2 = 0;
    _lastReset = 0;
    _entryCallback = nullptr;
    _exitCallback = nullptr;
}

void RFIDReaderManager::begin() {
    Serial.println("[RFID] Initializing...");
    
    // Init SPI
    SPI.begin(RFID_SCK, RFID_MISO, RFID_MOSI, -1);
    
    // Init RFID 1 (Entry)
    _rfid1 = new MFRC522(RFID1_SS, RFID1_RST);
    _rfid1->PCD_Init();
    byte v1 = _rfid1->PCD_ReadRegister(_rfid1->VersionReg);
    if (v1 == 0x00 || v1 == 0xFF) {
        Serial.println("[RFID] Reader 1 (Entry) NOT FOUND!");
    } else {
        Serial.printf("[RFID] Reader 1 (Entry) OK - Version: 0x%02X\n", v1);
    }
    
    // Init RFID 2 (Exit)
    _rfid2 = new MFRC522(RFID2_SS, RFID2_RST);
    _rfid2->PCD_Init();
    byte v2 = _rfid2->PCD_ReadRegister(_rfid2->VersionReg);
    if (v2 == 0x00 || v2 == 0xFF) {
        Serial.println("[RFID] Reader 2 (Exit) NOT FOUND!");
    } else {
        Serial.printf("[RFID] Reader 2 (Exit) OK - Version: 0x%02X\n", v2);
    }
    
    Serial.println("[RFID] Ready!");
}

void RFIDReaderManager::loop() {
    unsigned long now = millis();
    
    // Soft reset RFID định kỳ để tránh bị treo
    if (now - _lastReset > RFID_RESET_INTERVAL) {
        _softReset();
        _lastReset = now;
    }
    
    // Check RFID 1 (Entry)
    String card1 = _readCard(_rfid1);
    if (card1.length() > 0) {
        if (_isDebounced(card1, _lastCard1, _lastRead1)) {
            Serial.printf("[RFID] Entry card: %s\n", card1.c_str());
            if (_entryCallback) {
                _entryCallback(card1.c_str());
            }
        }
    }
    
    delay(10);
    
    // Check RFID 2 (Exit)
    String card2 = _readCard(_rfid2);
    if (card2.length() > 0) {
        if (_isDebounced(card2, _lastCard2, _lastRead2)) {
            Serial.printf("[RFID] Exit card: %s\n", card2.c_str());
            if (_exitCallback) {
                _exitCallback(card2.c_str());
            }
        }
    }
}

String RFIDReaderManager::_readCard(MFRC522* rfid) {
    if (rfid == nullptr) return "";
    
    // Reset antenna nếu cần
    rfid->PCD_SetAntennaGain(rfid->RxGain_max);
    
    if (!rfid->PICC_IsNewCardPresent()) {
        return "";
    }
    
    if (!rfid->PICC_ReadCardSerial()) {
        return "";
    }
    
    // Build UID string
    String uid = "";
    for (byte i = 0; i < rfid->uid.size; i++) {
        if (i > 0) uid += "-";
        if (rfid->uid.uidByte[i] < 0x10) uid += "0";
        uid += String(rfid->uid.uidByte[i], HEX);
    }
    uid.toUpperCase();
    
    // Halt card và stop crypto
    rfid->PICC_HaltA();
    rfid->PCD_StopCrypto1();
    
    return uid;
}

void RFIDReaderManager::_softReset() {
    // Soft reset cả 2 reader
    if (_rfid1) {
        _rfid1->PCD_Reset();
        _rfid1->PCD_Init();
        _rfid1->PCD_SetAntennaGain(_rfid1->RxGain_max);
    }
    if (_rfid2) {
        _rfid2->PCD_Reset();
        _rfid2->PCD_Init();
        _rfid2->PCD_SetAntennaGain(_rfid2->RxGain_max);
    }
    Serial.println("[RFID] Soft reset completed");
}

bool RFIDReaderManager::_isDebounced(const String& cardId, String& lastCard, unsigned long& lastRead) {
    unsigned long now = millis();
    
    // Same card within debounce time - ignore
    if (cardId == lastCard && (now - lastRead) < RFID_DEBOUNCE_TIME) {
        return false;
    }
    
    // Update last read
    lastCard = cardId;
    lastRead = now;
    return true;
}

void RFIDReaderManager::setEntryCallback(RFIDCallback callback) {
    _entryCallback = callback;
}

void RFIDReaderManager::setExitCallback(RFIDCallback callback) {
    _exitCallback = callback;
}
