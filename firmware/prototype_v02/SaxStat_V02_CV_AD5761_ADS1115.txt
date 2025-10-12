#include <SPI.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

// Pin definitions
#define CS_PIN    5   // AD5761 chip select (SPI)
#define SCK_PIN   18  // SPI clock
#define MOSI_PIN  23  // SPI MOSI
#define SDA_PIN   21  // I2C SDA for ADS1115
#define SCL_PIN   22  // I2C SCL for ADS1115

// AD5761 commands (from AD5761_Triangle_bipolar_1.5V_0.2Hz.txt)
#define CMD_WR_CTRL_REG       0x04  // Write control register
#define CMD_WR_UPDATE_DAC_REG 0x03  // Write and update DAC
#define CMD_SW_FULL_RESET     0x07  // Software reset
#define CMD_RD_CTRL_REG       0x05  // Read control register
#define CONTROL_REG_MINUS3_TO_PLUS3 0x005D  // -3V to +3V, straight binary
#define AD5761_CLOCK_RATE 1000000   // 1 MHz SPI

// CV Parameters (defaults, overridden by GUI)
float Vref = 2.5;           // ADR4525 Vref (V, measure to confirm)
float midpoint = 0.0;       // AD5761 midpoint (V)
float Vstart = 0.0;         // Start voltage after op-amp (V)
float Vend = 0.5;           // End voltage after op-amp (V)
float scanRate = 0.1;       // Scan rate (V/s)
int cycles = 1;             // Number of CV cycles
const float minAllowedVstart = -1.5; // Min Vstart (V)
const float maxAllowedVend = 1.5;    // Max Vend (V)

// Derived Parameters
const uint16_t maxDACValue = 65535; // 16-bit DAC
float minValueVoltage;              // DAC voltage for Vstart
float maxValueVoltage;              // DAC voltage for Vend
uint16_t minValue;                  // DAC value for Vstart
uint16_t maxValue;                  // DAC value for Vend
uint32_t halfCycleTimeMs;           // Half-cycle time (ms)
uint16_t stepSize;                  // DAC step size
uint32_t delayMs;                   // Delay per step (ms)

Adafruit_ADS1115 ads;               // ADS1115 instance
bool running = false;               // CV execution flag

// Initialize SPI and I2C
void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Initialize SPI for AD5761
    pinMode(CS_PIN, OUTPUT);
    digitalWrite(CS_PIN, HIGH);
    SPI.begin(SCK_PIN, -1, MOSI_PIN, CS_PIN);
    
    // Initialize I2C and ADS1115
    Wire.begin(SDA_PIN, SCL_PIN);
    if (!ads.begin(0x48)) { // I2C address 0x48 (ADDR to GND)
        Serial.println("Error: ADS1115 not found!");
        while (1);
    }
    ads.setGain(GAIN_ONE); // ±4.096V range
    
    // Initialize AD5761
    Serial.println("Starting AD5761 initialization...");
    ad5761_init();
    Serial.println("AD5761 initialized; VOUT set to 0 V");
    Serial.println("Ready for CV parameters...");
}

// Main loop
void loop() {
    // Check for serial input
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command.startsWith("START:")) {
            parseParameters(command);
            configureCV();
            running = true;
        } else if (command == "STOP") {
            running = false;
            ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768, 0); // Midpoint (0 V)
            Serial.println("Stopped CV, DAC set to 0 V");
        }
    }

    // Run CV if active
    if (running) {
        runCyclicVoltammetry();
        running = false;
        ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768, 0);
        Serial.println("CV completed, DAC set to 0 V");
    }
}

// Parse serial command for CV parameters
void parseParameters(String command) {
    int firstColon = command.indexOf(':');
    int secondColon = command.indexOf(':', firstColon + 1);
    int thirdColon = command.indexOf(':', secondColon + 1);
    int fourthColon = command.indexOf(':', thirdColon + 1);

    Vstart = command.substring(firstColon + 1, secondColon).toFloat();
    Vend = command.substring(secondColon + 1, thirdColon).toFloat();
    scanRate = command.substring(thirdColon + 1, fourthColon).toFloat();
    cycles = command.substring(fourthColon + 1).toInt();

    if (Vstart < minAllowedVstart || Vend > maxAllowedVend || scanRate <= 0 || cycles < 1) {
        Serial.println("Error: Invalid parameters!");
        running = false;
        ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768, 0);
        Serial.println("Error, DAC set to 0 V");
        return;
    }

    Serial.print("Received - Vstart: "); Serial.print(Vstart);
    Serial.print(" V, Vend: "); Serial.print(Vend);
    Serial.print(" V, Scan Rate: "); Serial.print(scanRate);
    Serial.print(" V/s, Cycles: "); Serial.println(cycles);
}

// Configure CV parameters
void configureCV() {
    // Map voltages to AD5761 (-3V to +3V, Vref = 2.5V)
    minValueVoltage = Vstart + midpoint; // e.g., 0 + 0 = 0 V
    maxValueVoltage = Vend + midpoint;   // e.g., 0.5 + 0 = 0.5 V
    minValue = (uint16_t)(((minValueVoltage + 3.0) / 6.0) * maxDACValue); // -1.5V = 16384
    maxValue = (uint16_t)(((maxValueVoltage + 3.0) / 6.0) * maxDACValue); // +1.5V = 49152

    float voltageRange = Vend - Vstart;
    halfCycleTimeMs = (uint32_t)((voltageRange / scanRate) * 1000); // e.g., 5000 ms
    stepSize = max(1, (maxValue - minValue) / 1000); // ~1000 steps
    uint32_t stepsPerHalf = (maxValue - minValue) / stepSize;
    delayMs = stepsPerHalf > 0 ? halfCycleTimeMs / stepsPerHalf : 1;

    Serial.print("minValue (DAC): "); Serial.println(minValue);
    Serial.print("maxValue (DAC): "); Serial.println(maxValue);
    Serial.print("Half-cycle time (ms): "); Serial.println(halfCycleTimeMs);
    Serial.print("Steps per half-cycle: "); Serial.println(stepsPerHalf);
    Serial.print("Delay per step (ms): "); Serial.println(delayMs);
}

// Run cyclic voltammetry
void runCyclicVoltammetry() {
    unsigned long lastStepTime = 0;
    for (int cycle = 0; cycle < cycles && running; cycle++) {
        uint16_t value = minValue;
        bool rising = true;

        while (running) {
            unsigned long currentTime = millis();
            if (currentTime - lastStepTime >= delayMs) {
                ad5761_write(CMD_WR_UPDATE_DAC_REG, value, 0);

                // Read ADS1115
                int16_t adcValue = ads.readADC_SingleEnded(0);
                float volts = adcValue * 4.096 / 32768;
                if (adcValue >= -32768 && adcValue <= 32767) {
                    Serial.print(volts); Serial.print(",");
                    float current = -(volts - 0.0) / (40000 / 1e6); // 40 kΩ, V_offset = 0 V
                    Serial.println(current);
                } else {
                    Serial.println("ADC:ERROR");
                }

                if (rising) {
                    if (value + stepSize > maxValue) {
                        value = maxValue;
                        rising = false;
                    } else {
                        value += stepSize;
                    }
                } else {
                    if (value < minValue + stepSize) {
                        value = minValue;
                        rising = true;
                        break;
                    } else {
                        value -= stepSize;
                    }
                }
                lastStepTime = currentTime;
            }

            // Check for STOP command
            if (Serial.available() > 0) {
                String command = Serial.readStringUntil('\n');
                command.trim();
                if (command == "STOP") {
                    running = false;
                    ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768, 0);
                    Serial.println("Stopped CV, DAC set to 0 V");
                    break;
                }
            }
        }
    }
}

// AD5761 write function
void ad5761_write(uint8_t reg_addr_cmd, uint16_t reg_data, char cs) {
    uint8_t tx_data[3] = {
        reg_addr_cmd,
        (reg_data >> 8) & 0xFF,
        reg_data & 0xFF
    };
    SPI.beginTransaction(SPISettings(AD5761_CLOCK_RATE, MSBFIRST, SPI_MODE2));
    digitalWrite(CS_PIN, LOW);
    SPI.transfer(tx_data, 3);
    digitalWrite(CS_PIN, HIGH);
    SPI.endTransaction();
    delayMicroseconds(1);
}

// AD5761 read function
uint16_t ad5761_read(uint8_t reg_addr_cmd) {
    uint8_t tx_data[3] = { reg_addr_cmd, 0, 0 };
    uint8_t rx_data[3] = { 0, 0, 0 };
    SPI.beginTransaction(SPISettings(AD5761_CLOCK_RATE, MSBFIRST, SPI_MODE2));
    digitalWrite(CS_PIN, LOW);
    SPI.transfer(tx_data, 3);
    digitalWrite(CS_PIN, HIGH);
    delayMicroseconds(1);
    digitalWrite(CS_PIN, LOW);
    SPI.transfer(rx_data, 3);
    digitalWrite(CS_PIN, HIGH);
    SPI.endTransaction();
    return ((uint16_t)rx_data[1] << 8) | rx_data[2];
}

// Initialize AD5761
void ad5761_init() {
    Serial.println("Sending software full reset...");
    ad5761_write(CMD_SW_FULL_RESET, 0, 0);
    Serial.println("Writing control register (0x005D for -3 V to +3 V)...");
    ad5761_write(CMD_WR_CTRL_REG, CONTROL_REG_MINUS3_TO_PLUS3, 0);
    Serial.println("Reading back control register...");
    uint16_t ctrl_reg = ad5761_read(CMD_RD_CTRL_REG);
    Serial.print("Control register value: 0x");
    Serial.println(ctrl_reg, HEX);
    Serial.println("Setting DAC to 0 V (0x8000)...");
    ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768, 0);
}