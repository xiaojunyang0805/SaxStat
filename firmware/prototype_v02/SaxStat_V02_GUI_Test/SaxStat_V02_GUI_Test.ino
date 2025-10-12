// The program is for ESP32 driving a potentiostat with AD5761 DAC and internal ADC, interacting with a Python GUI.
#include <SPI.h>

#define SCK_PIN 18
#define MOSI_PIN 23
#define CS_PIN 5    // AD5761 CS pin
#define AD5761_CLOCK_RATE 10000000 // 10 MHz
#define ADC_PIN 34  // ESP32 ADC pin (GPIO34)

#define CMD_WR_CTRL_REG 0x4
#define CMD_WR_UPDATE_DAC_REG 0x3
#define CMD_SW_FULL_RESET 0xF
#define CONTROL_REG_MINUS3_TO_PLUS3 0x005D // ±3V range, straight binary

const uint16_t MIN_DAC_CODE = 15934; // -1.5V
const uint16_t MAX_DAC_CODE = 49602; // +1.5V

SPIClass spi(HSPI);

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

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  Serial.println("Starting SaxStat V02 AD5761-ESP32 ADC Test...");

  pinMode(ADC_PIN, INPUT);
  // Removed initial ADC read to avoid stale messages
  spi.begin(SCK_PIN, -1, MOSI_PIN, CS_PIN);
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  ad5761_write(CMD_SW_FULL_RESET, 0x0000);
  delay(10);
  ad5761_write(CMD_WR_CTRL_REG, CONTROL_REG_MINUS3_TO_PLUS3);
  delay(10);
  ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // 0V
  delay(5000);
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

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      String command = inputBuffer;
      inputBuffer = "";
      command.trim();
      Serial.print("Received: "); Serial.println(command);
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
          if (startVoltage < -1.5 || endVoltage > 1.5 || scanRate <= 0 || cycles < 1) {
            Serial.println("Error: Parameters out of range (-1.5V to 1.5V) or invalid!");
            running = false;
            ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Reset to 0V
            return;
          }
          running = true;
          minValue = mapVoltageToDAC(startVoltage);
          maxValue = mapVoltageToDAC(endVoltage);
          float voltageRange = abs(endVoltage - startVoltage);
          halfCycleTimeMs = (uint32_t)((voltageRange / scanRate) * 1000);
          stepSize = max(1, (maxValue - minValue) / 1000);
          uint32_t stepsPerHalf = (maxValue - minValue) / stepSize;
          delayMs = stepsPerHalf > 0 ? halfCycleTimeMs / stepsPerHalf : 1;
          skippedSamples = 0;
          Serial.println("Applied Parameters"); // Added for GUI compatibility
          Serial.print("minValue (DAC): "); Serial.println(minValue);
          Serial.print("maxValue (DAC): "); Serial.println(maxValue);
          Serial.print("Half-cycle time (ms): "); Serial.println(halfCycleTimeMs);
          Serial.print("Steps per half-cycle: "); Serial.println(stepsPerHalf);
          Serial.print("Delay per step (ms): "); Serial.println(delayMs);
        }
      } else if (command == "STOP") {
        running = false;
        ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Reset to 0V
        Serial.println("CV stopped.");
      } else if (command == "RESET_GPIO34:0") {
        ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Set DAC to 0V
        Serial.println("DAC set to 0V");
      } else if (command == "CALIBRATE") {
        int adcValue = analogRead(ADC_PIN);
        if (adcValue >= 0 && adcValue <= 4095) {
          Serial.println(adcValue);
        } else {
          Serial.println("ADC:ERROR");
        }
      } else if (command == "READ_INITIAL") {
        int adcValue = analogRead(ADC_PIN);
        Serial.print("Initial ADC voltage: "); Serial.print(adcValue * 3.3 / 4095); Serial.println(" V");
      }
    } else {
      inputBuffer += c;
    }
  }

  if (running) {
    static uint16_t value = minValue;
    static bool rising = true;
    static unsigned long lastStepTime = 0;

    for (int cycle = 0; cycle < cycles && running; cycle++) {
      while (running) {
        unsigned long currentTime = millis();
        if (currentTime - lastStepTime >= delayMs) {
          ad5761_write(CMD_WR_UPDATE_DAC_REG, value);
          if (cycle == 0 && rising && value == minValue) {
            delay(100); // 100 ms settling time
          }
          int adcValue = analogRead(ADC_PIN);
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
          } else if (command == "RESET_GPIO34:0") {
            ad5761_write(CMD_WR_UPDATE_DAC_REG, 32768); // Set DAC to 0V
            Serial.println("DAC set to 0V");
          } else if (command == "CALIBRATE") {
            int adcValue = analogRead(ADC_PIN);
            if (adcValue >= 0 && adcValue <= 4095) {
              Serial.println(adcValue);
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