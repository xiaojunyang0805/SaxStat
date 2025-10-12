//This firmware enables CV test controlled by "SaxStat_GUI_V03". It sets TIA resistor of 10K ohm. 
//DAC chip AD5761 for generating CV voltages. ADC chip ADS1115 for collecting voltage signals after TIA.
//Debugging is done on 2025-09-04 to enable DAC resumes to start from minValue voltage after re-start command. 
//Debugging is done on 2025-09-04 to enable initial_voltage is larger than end_voltage.

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

#define SCK_PIN 18
#define MOSI_PIN 23
#define CS_PIN 5    // AD5761 CS pin
#define AD5761_CLOCK_RATE 10000000 // 10 MHz

#define CMD_WR_CTRL_REG 0x4
#define CMD_WR_UPDATE_DAC_REG 0x3
#define CMD_SW_FULL_RESET 0xF
#define CONTROL_REG_MINUS3_TO_PLUS3 0x005D // ±3V range, straight binary

const uint16_t MIN_DAC_CODE = 15934; // -1.5V
const uint16_t MAX_DAC_CODE = 49602; // +1.5V

SPIClass spi(HSPI);
Adafruit_ADS1115 ads;  // ADS1115 instance

void ad5761_write(uint8_t reg_addr_cmd, uint16_t reg_data) {
  uint8_t tx_data[3] = {reg_addr_cmd, (reg_data >> 8) & 0xFF, reg_data & 0xFF};
  spi.beginTransaction(SPISettings(AD5761_CLOCK_RATE, MSBFIRST, SPI_MODE2));
  digitalWrite(CS_PIN, LOW);
  spi.transfer(tx_data, 3);
  digitalWrite(CS_PIN, HIGH);
  spi.endTransaction();
  delayMicroseconds(1);
}

uint16_t mapVoltageToDAC(float voltage) {
  if (voltage <= -1.5) return MIN_DAC_CODE;
  if (voltage >= 1.5) return MAX_DAC_CODE;
  return MIN_DAC_CODE + ((voltage + 1.5) / 3.0) * (MAX_DAC_CODE - MIN_DAC_CODE);
}

float mapDACToVoltage(uint16_t dacCode) {
  if (dacCode <= MIN_DAC_CODE) return -1.5;
  if (dacCode >= MAX_DAC_CODE) return 1.5;
  return -1.5 + ((dacCode - MIN_DAC_CODE) / (float)(MAX_DAC_CODE - MIN_DAC_CODE)) * 3.0;
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("Starting SaxStat V03 AD5761-ADS1115 Test...");

  spi.begin(SCK_PIN, -1, MOSI_PIN, CS_PIN);
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  ad5761_write(CMD_SW_FULL_RESET, 0x0000);
  delay(10);
  ad5761_write(CMD_WR_CTRL_REG, CONTROL_REG_MINUS3_TO_PLUS3);
  delay(10);
  ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // 0V
  delay(5000);

  // Enhanced ADS1115 initialization
  Wire.begin(); // Default SDA (21) and SCL (22)
  Wire.setClock(100000); // Standard 100 kHz
  Serial.println("Scanning I2C bus...");
  bool adsFound = false;
  for (uint8_t addr : {0x48, 0x49, 0x4A, 0x4B}) {
    Wire.beginTransmission(addr);
    int error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("I2C device found at 0x");
      Serial.println(addr, HEX);
      if (ads.begin(addr)) {
        adsFound = true;
        Serial.print("ADS1115 initialized at address 0x");
        Serial.println(addr, HEX);
        ads.setGain(GAIN_ONE); // ±4.096V range
        break;
      }
    }
  }
  if (!adsFound) {
    Serial.println("Error: ADS1115 not found at any address (0x48-0x4B)!");
    while (1) {
      delay(10);
    }
  }

  // Initial virtual Vramp for verification
  uint16_t initialDAC = 32768; // 0V
  float initialVramp = mapDACToVoltage(initialDAC);
  Serial.print("Initial Virtual Vramp (DAC): ");
  Serial.print(initialVramp);
  Serial.println(" V");
}

void loop() {
  static String inputBuffer = "";
  static bool running = false;
  static float startVoltage = -1.5;
  static float endVoltage = 1.5;
  static float scanRate = 0.1;
  static int cycles = 1;
  static uint16_t minValue = MIN_DAC_CODE;
  static uint16_t maxValue = MAX_DAC_CODE;
  static uint32_t halfCycleTimeMs = 0;
  static uint16_t stepSize = 1;
  static uint32_t delayMs = 1;
  static int initialSkipCount = 50;
  static int skippedSamples = 0;

  // Ramp state
  static uint16_t value;
  static bool rising;
  static unsigned long lastStepTime;

  // NEW: For first-step settling, regardless of direction
  static bool firstStep;

  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      String command = inputBuffer;
      inputBuffer = "";
      command.trim();
      Serial.print("Received: ");
      Serial.println(command);
      if (command.startsWith("START:")) {
        int index1 = command.indexOf(':') + 1;
        int index2 = command.indexOf(':', index1);
        int index3 = command.indexOf(':', index2 + 1);
        int index4 = command.indexOf(':', index3 + 1);
        if (index1 > 0 && index2 > 0 && index3 > 0 && index4 > 0) {
          startVoltage = command.substring(index1, index2).toFloat();
          endVoltage = command.substring(index2 + 1, index3).toFloat();
          scanRate = command.substring(index3 + 1, index4).toFloat();
          cycles = command.substring(index4 + 1).toInt();
          Serial.print("Parsed: start=");
          Serial.print(startVoltage);
          Serial.print(", end=");
          Serial.print(endVoltage);
          Serial.print(", rate=");
          Serial.print(scanRate);
          Serial.print(", cycles=");
          Serial.println(cycles);
          if (startVoltage < -1.5 || endVoltage > 1.5 || startVoltage > 1.5 || endVoltage < -1.5 || scanRate <= 0 || cycles < 1) {
            Serial.println("Error: Parameters out of range (-1.5V to 1.5V) or invalid!");
            running = false;
            ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Reset to 0V
            return;
          }
          running = true;

          // NEW: Handle start > end by setting initial direction and true min/max
          uint16_t dac_start = mapVoltageToDAC(startVoltage);
          uint16_t dac_end = mapVoltageToDAC(endVoltage);
          minValue = min(dac_start, dac_end);
          maxValue = max(dac_start, dac_end);

          if (dac_start <= dac_end) {
            value = minValue;  // Start low, rising
            rising = true;
          } else {
            value = maxValue;  // Start high, falling
            rising = false;
          }

          float voltageRange = abs(endVoltage - startVoltage);
          halfCycleTimeMs = static_cast<uint32_t>((voltageRange / scanRate) * 1000);
          stepSize = max(1, (maxValue - minValue) / 1000);  // Use abs difference
          uint32_t stepsPerHalf = (maxValue - minValue) / stepSize;
          delayMs = stepsPerHalf > 0 ? halfCycleTimeMs / stepsPerHalf : 1;
          if (delayMs == 0) delayMs = 1;
          skippedSamples = 0;
          firstStep = true;  // NEW: Reset for initial settling
          lastStepTime = millis();

          Serial.println("Applied Parameters");
          Serial.print("minValue (DAC): ");
          Serial.println(minValue);
          Serial.print("maxValue (DAC): ");
          Serial.println(maxValue);
          Serial.print("Initial value (DAC): ");
          Serial.println(value);
          Serial.print("Initial direction: ");
          Serial.println(rising ? "rising" : "falling");
          Serial.print("Half-cycle time (ms): ");
          Serial.println(halfCycleTimeMs);
          Serial.print("Steps per half-cycle: ");
          Serial.println(stepsPerHalf);
          Serial.print("Delay per step (ms): ");
          Serial.println(delayMs);
        } else {
          Serial.println("Error: Invalid START command format!");
        }
      } else if (command == "STOP") {
        running = false;
        ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Reset to 0V
        Serial.println("CV stopped.");
      } else if (command == "CALIBRATE") {
        int16_t vout_d = ads.readADC_SingleEnded(0);
        if (vout_d >= 0) {
          Serial.println(vout_d);
        } else {
          Serial.println("ADC:ERROR");
        }
      } else if (command == "RESET_GPIO34:0") {
        // Ignore this command as GPIO34 is no longer used
        Serial.println("GPIO34 reset command received (ignored, not in use)");
      }
    } else {
      inputBuffer += c;
    }
  }

  if (running) {
    Serial.println("Entering acquisition loop"); // Debug entry
    for (int cycle = 0; cycle < cycles && running; cycle++) {
      while (running) {
        unsigned long currentTime = millis();
        if (currentTime - lastStepTime >= delayMs) {
          ad5761_write(CMD_WR_UPDATE_DAC_REG, value);
          float virtualVramp = mapDACToVoltage(value); // Calculate virtual Vramp
          Serial.print("Writing DAC value: "); Serial.print(value);
          Serial.print(", Virtual Vramp: "); Serial.println(virtualVramp, 3); // Debug

          // NEW: Settling time for first step only, regardless of direction
          if (firstStep) {
            delay(100); // 100 ms settling time
            firstStep = false;
          }

          int16_t vout_d = ads.readADC_SingleEnded(0); // Read from ADS1115
          Serial.print("Read ADS1115 - vout_d: "); Serial.println(vout_d); // Debug ADS1115 read
          if (vout_d >= 0) {
            // NEW: Skip transients in first cycle's initial steps, regardless of direction
            if (cycle == 0 && skippedSamples < initialSkipCount) {
              skippedSamples++;
              Serial.println("Skipping transient data");
            } else {
              Serial.println(vout_d);
            }
          } else {
            Serial.println("ADC:ERROR");
          }
          if (rising) {
            if (value >= maxValue) {
              value = maxValue;
              rising = false;
            } else {
              value += stepSize;
            }
          } else {
            if (value <= minValue) {
              value = minValue;
              rising = true;
              break;
            } else {
              value -= stepSize;
            }
          }
          lastStepTime = currentTime;
        }
        if (Serial.available() > 0) {
          String command = Serial.readStringUntil('\n');
          command.trim();
          if (command == "STOP") {
            running = false;
            ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Reset to 0V
            Serial.println("CV stopped.");
            break;
          } else if (command == "CALIBRATE") {
            int16_t vout_d = ads.readADC_SingleEnded(0);
            if (vout_d >= 0) {
              Serial.println(vout_d);
            } else {
              Serial.println("ADC:ERROR");
            }
          } 
        }
      }
    }
    running = false;
    ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Reset to 0V
    Serial.println("CV complete.");
  }
}