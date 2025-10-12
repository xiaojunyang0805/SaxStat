#include <SPI.h>

const int CS_PIN = 5;  // Chip Select pin for MAX5443
const int adcPin = 34; // GPIO34 for ADC input

// SPI Settings
SPISettings spiSettings(1000000, MSBFIRST, SPI_MODE0); // 1 MHz, Mode 0

// Cyclic Voltammetry Parameters (defaults, overridden by GUI)
float Vref = 3.0;           // MAX5443 Vref (V, MEASURE AND UPDATE)
float midpoint = 1.5;      // Midpoint voltage subtracted by op-amp (V, MEASURE AND UPDATE)
float Vstart = 0;           // Start voltage after op-amp (V)
float Vend = 0.5;           // End voltage after op-amp (V)
float scanRate = 0.1;       // Scan rate (V/s)
int cycles = 1;             // Number of CV cycles
const float minAllowedVstart = -1.0; // Allowed minimum Vstart (V)
const float maxAllowedVend = 1.0;    // Allowed maximum Vend (V)

// Derived Parameters
const uint16_t maxDACValue = 65535; // 16-bit DAC maximum value
float minValueVoltage;              // DAC voltage for Vstart (V)
float maxValueVoltage;              // DAC voltage for Vend (V)
uint16_t minValue;                  // DAC value for Vstart
uint16_t maxValue;                  // DAC value for Vend
uint32_t halfCycleTimeMs;           // Half-cycle time (ms)
uint16_t stepSize;                  // Step size for DAC increments (dynamic)
uint32_t delayMs;                   // Delay per step (ms)

bool running = false;               // Flag to control CV execution
int initialSkipCount = 5;           // Number of initial samples to skip

void setup() {
    SPI.begin(); // Initialize SPI
    pinMode(CS_PIN, OUTPUT);
    digitalWrite(CS_PIN, HIGH); // Ensure CS is high initially
    
    Serial.begin(115200);
    while (!Serial) {
        delay(10); // Wait for serial
    }
    analogReadResolution(12); // Set ADC to 12-bit (0-4095)

    // Initialize DAC
    uint16_t midpointValue = (uint16_t)((midpoint / Vref) * maxDACValue);
    sendToDAC(midpointValue);
    Serial.print("Initialized DAC to midpoint value: "); Serial.println(midpointValue);
    Serial.print("Expected V_DAC: "); Serial.println((midpointValue / (float)maxDACValue) * Vref);

    Serial.println("Ready for CV parameters...");
}

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
            uint16_t midpointValue = (uint16_t)((midpoint / Vref) * maxDACValue);
            sendToDAC(midpointValue);
            Serial.print("Stopped CV, DAC set to midpoint value: "); Serial.println(midpointValue);
            Serial.println("CV stopped.");
        }
    }

    // Run CV if active
    if (running) {
        runCyclicVoltammetry();
        running = false;
        uint16_t midpointValue = (uint16_t)((midpoint / Vref) * maxDACValue);
        sendToDAC(midpointValue);
        Serial.print("CV completed, DAC set to midpoint value: "); Serial.println(midpointValue);
        Serial.println("CV complete.");
    }
}

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
        uint16_t midpointValue = (uint16_t)((midpoint / Vref) * maxDACValue);
        sendToDAC(midpointValue);
        Serial.print("Error, DAC set to midpoint value: "); Serial.println(midpointValue);
        return;
    }

    Serial.print("Received - Vstart: "); Serial.print(Vstart);
    Serial.print(" V, Vend: "); Serial.print(Vend);
    Serial.print(" V, Scan Rate: "); Serial.print(scanRate);
    Serial.print(" V/s, Cycles: "); Serial.println(cycles);
}

void configureCV() {
    minValueVoltage = Vstart + midpoint;
    maxValueVoltage = Vend + midpoint;
    minValue = (uint16_t)((minValueVoltage / Vref) * maxDACValue);
    maxValue = (uint16_t)((maxValueVoltage / Vref) * maxDACValue);

    float voltageRange = Vend - Vstart;
    halfCycleTimeMs = (uint32_t)((voltageRange / scanRate) * 1000);
    stepSize = max(1, (maxValue - minValue) / 1000);
    uint32_t stepsPerHalf = (maxValue - minValue) / stepSize;
    delayMs = stepsPerHalf > 0 ? halfCycleTimeMs / stepsPerHalf : 1;

    Serial.print("minValue (DAC): "); Serial.println(minValue);
    Serial.print("maxValue (DAC): "); Serial.println(maxValue);
    Serial.print("Half-cycle time (ms): "); Serial.println(halfCycleTimeMs);
    Serial.print("Steps per half-cycle: "); Serial.println(stepsPerHalf);
    Serial.print("Delay per step (ms): "); Serial.println(delayMs);
}

void runCyclicVoltammetry() {
    unsigned long lastStepTime = 0;
    int skippedSamples = 0;
    for (int cycle = 0; cycle < cycles && running; cycle++) {
        uint16_t value = minValue;
        bool rising = true;

        while (running) {
            unsigned long currentTime = millis();
            if (currentTime - lastStepTime >= delayMs) {
                sendToDAC(value);

                // Initial settling delay and skip
                if (cycle == 0 && rising && value == minValue) {
                    delay(100); // 100 ms settling time
                }

                int adcValue = analogRead(adcPin);
                if (adcValue >= 0 && adcValue <= 4095) {
                    if (cycle == 0 && rising && skippedSamples < initialSkipCount) {
                        skippedSamples++;
                        Serial.println("Skipping transient data");
                    } else {
                        Serial.println(adcValue);
                    }
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
                    uint16_t midpointValue = (uint16_t)((midpoint / Vref) * maxDACValue);
                    sendToDAC(midpointValue);
                    Serial.print("Stopped CV, DAC set to midpoint value: "); Serial.println(midpointValue);
                    Serial.println("CV stopped.");
                    break;
                }
            }
        }
    }
}

void sendToDAC(uint16_t value) {
    Serial.print("Sending DAC value: "); Serial.println(value);
    digitalWrite(CS_PIN, LOW);
    SPI.beginTransaction(spiSettings);
    SPI.transfer16(value);
    SPI.endTransaction();
    digitalWrite(CS_PIN, HIGH);
}