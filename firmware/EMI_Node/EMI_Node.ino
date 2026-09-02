#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_BME280.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ModbusRTUSlave.h>


// =====================================================
// MODBUS / RS485
// =====================================================

const uint8_t MODBUS_SLAVE_ID = 1;

const uint8_t DE_PIN = 3;
const uint8_t RE_PIN = 2;

ModbusRTUSlave modbus(Serial, DE_PIN, RE_PIN);


// =====================================================
// MODBUS HOLDING REGISTERS
// =====================================================

uint16_t holdingRegisters[9];


// =====================================================
// DS18B20
// =====================================================

#define ONE_WIRE_BUS 5

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

DeviceAddress senzorFront = {
  0x28, 0x48, 0x69, 0x7C, 0x00, 0x00, 0x00, 0x92
};

DeviceAddress senzorRear = {
  0x28, 0x31, 0xDD, 0x7B, 0x00, 0x00, 0x00, 0x4A
};

DeviceAddress senzorPVBifacial = {
  0x28, 0xC5, 0xE7, 0xA7, 0x07, 0x00, 0x00, 0xB4
};


// =====================================================
// INA219
// =====================================================

Adafruit_INA219 ina219_Front(0x40);
Adafruit_INA219 ina219_Rear(0x41);


// =====================================================
// BME280
// =====================================================

Adafruit_BME280 bme;


// =====================================================
// TIMING
// =====================================================

const unsigned long MEASUREMENT_INTERVAL = 5000UL;

unsigned long lastMeasurement = 0;


// =====================================================
// SETUP
// =====================================================

void setup() {

  // ---------------------------------------------------
  // Sensors
  // ---------------------------------------------------

  sensors.begin();

  ina219_Front.begin();
  ina219_Front.setCalibration_16V_400mA();

  ina219_Rear.begin();
  ina219_Rear.setCalibration_16V_400mA();

  bme.begin(0x76);


  // ---------------------------------------------------
  // Modbus
  // ---------------------------------------------------

  modbus.configureHoldingRegisters(
    holdingRegisters,
    9
  );

  Serial.begin(9600);

  modbus.begin(
    MODBUS_SLAVE_ID,
    9600,
    SERIAL_8N1
  );


  // ---------------------------------------------------
  // Initial register values
  // ---------------------------------------------------

  for (uint8_t i = 0; i < 9; i++) {
    holdingRegisters[i] = 0;
  }
}


// =====================================================
// LOOP
// =====================================================

void loop() {

  // ===================================================
  // MODBUS POLL
  // ===================================================
  //
  // IMPORTANT:
  // Keep this call continuously active.
  //
  // ===================================================

  modbus.poll();


  // ===================================================
  // SENSOR ACQUISITION
  // ===================================================

  if (millis() - lastMeasurement >= MEASUREMENT_INTERVAL) {

    lastMeasurement = millis();


    // -------------------------------------------------
    // DS18B20
    // -------------------------------------------------

    sensors.requestTemperatures();

    float tempFront =
      sensors.getTempC(senzorFront);

    float tempRear =
      sensors.getTempC(senzorRear);

    float tempPVBifacial =
      sensors.getTempC(senzorPVBifacial);


    // -------------------------------------------------
    // INA219
    // -------------------------------------------------

    float current_mA_F =
      ina219_Front.getCurrent_mA();

      if (current_mA_F < 0.0) 
        {
        current_mA_F = 0.0;
         }
delay(50);
    float current_mA_R =
      ina219_Rear.getCurrent_mA();

    if (current_mA_R < 0.0) 
    {
        current_mA_R = 0.0;
      }
delay(50);

    // -------------------------------------------------
    // BME280
    // -------------------------------------------------

    float bmeTemp =
      bme.readTemperature();
delay(10);
    float bmeHum =
      bme.readHumidity();
delay(10);
    float bmePres =
      bme.readPressure() / 100.0F;
delay(10);

    // =================================================
    // UPDATE MODBUS REGISTERS
    // =================================================

    // -------------------------------------------------
    // DS18B20 temperatures ×100
    // -------------------------------------------------

    if (tempFront != DEVICE_DISCONNECTED_C) {

      holdingRegisters[0] =
        (uint16_t)(int16_t)(tempFront * 100.0);
    }


    if (tempRear != DEVICE_DISCONNECTED_C) {

      holdingRegisters[1] =
        (uint16_t)(int16_t)(tempRear * 100.0);
    }


    if (tempPVBifacial != DEVICE_DISCONNECTED_C) {

      holdingRegisters[2] =
        (uint16_t)(int16_t)(tempPVBifacial * 100.0);
    }


    // -------------------------------------------------
    // INA219 currents ×100
    // -------------------------------------------------

    holdingRegisters[3] =
      (uint16_t)(current_mA_F * 100.0);


    holdingRegisters[4] =
      (uint16_t)(current_mA_R * 100.0);


    // -------------------------------------------------
    // BME280
    // -------------------------------------------------

    if (!isnan(bmeTemp)) {

      holdingRegisters[5] =
        (uint16_t)(int16_t)(bmeTemp * 100.0);
    }


    if (!isnan(bmeHum)) {

      holdingRegisters[6] =
        (uint16_t)(bmeHum * 100.0);
    }


    if (!isnan(bmePres)) {

      holdingRegisters[7] =
        (uint16_t)(bmePres * 10.0);
    }


    // -------------------------------------------------
    // Arduino uptime
    // -------------------------------------------------

    holdingRegisters[8] =
      (uint16_t)(millis() / 1000UL);
  }
}