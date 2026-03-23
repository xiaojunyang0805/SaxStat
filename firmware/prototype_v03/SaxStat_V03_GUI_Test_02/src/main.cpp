#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

#define SCK_PIN 18
#define MOSI_PIN 23
#define CS_PIN 5    // AD5761 CS pin
#define AD5761_CLOCK_RATE 10000000 // 10 MHz

#define GAIN1_PIN 33
#define GAIN2_PIN 25

#define CMD_WR_CTRL_REG 0x4
#define CMD_WR_UPDATE_DAC_REG 0x3
#define CMD_SW_FULL_RESET 0xF
#define CONTROL_REG_MINUS3_TO_PLUS3 0x005D // ±3V range, straight binary

const uint16_t MIN_DAC_CODE = 15934; // -1.5V
const uint16_t MAX_DAC_CODE = 49602; // +1.5V
const uint16_t ZERO_DAC_CODE = 32768; // 0V

SPIClass spi(HSPI);
Adafruit_ADS1115 ads;

// Global state
static bool running = false;
static int currentMode = 0;

// ==================== Hardware helpers ====================

void ad5761_write(uint8_t reg_addr_cmd, uint16_t reg_data) {
  uint8_t tx_data[3] = {reg_addr_cmd, (uint8_t)((reg_data >> 8) & 0xFF), (uint8_t)(reg_data & 0xFF)};
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

void resetDAC() {
  ad5761_write(CMD_WR_UPDATE_DAC_REG, ZERO_DAC_CODE);
}

// Set DAC and read ADC, send DATA line. Returns false if ADC error.
bool setAndMeasure(float voltage, int* skipCount) {
  uint16_t dacCode = mapVoltageToDAC(voltage);
  ad5761_write(CMD_WR_UPDATE_DAC_REG, dacCode);
  float vramp = mapDACToVoltage(dacCode);
  int16_t vout_d = ads.readADC_SingleEnded(0);
  if (vout_d >= 0) {
    if (*skipCount > 0) {
      (*skipCount)--;
    } else {
      Serial.print("DATA:");
      Serial.print(vramp, 4);
      Serial.print(",");
      Serial.println(vout_d);
    }
    return true;
  }
  return false;
}

// Check for STOP or MODE commands during acquisition
bool checkSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "STOP") {
      running = false;
      resetDAC();
      Serial.println("Stopped.");
      return true;
    } else if (command == "MODE_0") {
      currentMode = 0;
      digitalWrite(GAIN1_PIN, LOW);
      digitalWrite(GAIN2_PIN, LOW);
    } else if (command == "MODE_1") {
      currentMode = 1;
      digitalWrite(GAIN1_PIN, HIGH);
      digitalWrite(GAIN2_PIN, HIGH);
    }
  }
  return false;
}

// Sweep DAC between two values. Returns false if stopped.
bool sweepSegment(uint16_t fromDAC, uint16_t toDAC, uint16_t stepSize,
                  uint32_t delayMs, int* skipCount) {
  bool goingUp = (toDAC > fromDAC);
  uint16_t value = fromDAC;
  unsigned long lastStepTime = 0;

  while (running) {
    unsigned long now = millis();
    if (now - lastStepTime >= delayMs) {
      ad5761_write(CMD_WR_UPDATE_DAC_REG, value);
      float vramp = mapDACToVoltage(value);
      int16_t vout_d = ads.readADC_SingleEnded(0);
      if (vout_d >= 0) {
        if (*skipCount > 0) { (*skipCount)--; }
        else {
          Serial.print("DATA:");
          Serial.print(vramp, 4);
          Serial.print(",");
          Serial.println(vout_d);
        }
      }
      if (goingUp) {
        if (value >= toDAC) break;
        value += stepSize;
        if (value > toDAC) value = toDAC;
      } else {
        if (value <= toDAC) break;
        value = (value - toDAC < stepSize) ? toDAC : value - stepSize;
      }
      lastStepTime = now;
    }
    if (checkSerialCommands()) return false;
  }
  return running;
}

// ==================== Helper: parse colon-separated floats ====================

int parseFields(const String& cmd, int startIdx, float* fields, int maxFields) {
  int count = 0;
  int pos = startIdx;
  while (count < maxFields && pos < (int)cmd.length()) {
    int next = cmd.indexOf(':', pos);
    if (next < 0) {
      fields[count++] = cmd.substring(pos).toFloat();
      break;
    } else {
      fields[count++] = cmd.substring(pos, next).toFloat();
      pos = next + 1;
    }
  }
  return count;
}

// ==================== Experiment handlers ====================

// CV: START:<initial_v>:<high_v>:<low_v>:<scan_rate>:<cycles>
void handleCV(const String& cmd) {
  float f[5];
  int n = parseFields(cmd, cmd.indexOf(':') + 1, f, 5);
  if (n < 5) { Serial.println("Error: CV needs 5 params"); return; }

  float initialV = f[0], highV = f[1], lowV = f[2], scanRate = f[3];
  int cycles = (int)f[4];

  if (lowV < -1.5 || highV > 1.5 || lowV >= highV ||
      initialV < lowV || initialV > highV || scanRate <= 0 || cycles < 1) {
    Serial.println("Error: Parameters out of range!"); resetDAC(); return;
  }

  uint16_t initDAC = mapVoltageToDAC(initialV);
  uint16_t highDAC = mapVoltageToDAC(highV);
  uint16_t lowDAC  = mapVoltageToDAC(lowV);

  uint16_t dacRange = highDAC - lowDAC;
  uint16_t stepSize = max((uint16_t)1, (uint16_t)(dacRange / 1000));
  uint32_t halfCycleTimeMs = (uint32_t)(((highV - lowV) / scanRate) * 1000);
  uint32_t stepsPerHalf = dacRange / stepSize;
  uint32_t delayMs = stepsPerHalf > 0 ? halfCycleTimeMs / stepsPerHalf : 1;
  if (delayMs == 0) delayMs = 1;

  ad5761_write(CMD_WR_UPDATE_DAC_REG, initDAC);
  delay(200);

  running = true;
  int skipCount = 50;
  Serial.println("START_CONFIRMED");

  if (initDAC < highDAC)
    if (!sweepSegment(initDAC, highDAC, stepSize, delayMs, &skipCount)) goto done;

  for (int c = 0; c < cycles && running; c++) {
    if (!sweepSegment(highDAC, lowDAC, stepSize, delayMs, &skipCount)) goto done;
    if (!sweepSegment(lowDAC, highDAC, stepSize, delayMs, &skipCount)) goto done;
  }

  if (initDAC < highDAC)
    if (!sweepSegment(highDAC, initDAC, stepSize, delayMs, &skipCount)) goto done;

done:
  running = false;
  resetDAC();
  Serial.println("CV complete.");
}

// CA: CA:<potential>:<duration>:<sample_interval>
void handleCA(const String& cmd) {
  float f[3];
  int n = parseFields(cmd, cmd.indexOf(':') + 1, f, 3);
  if (n < 3) { Serial.println("Error: CA needs 3 params"); return; }

  float potential = f[0], duration = f[1], interval = f[2];

  if (potential < -1.5 || potential > 1.5 || duration <= 0 || interval <= 0) {
    Serial.println("Error: Parameters out of range!"); resetDAC(); return;
  }

  uint16_t dacCode = mapVoltageToDAC(potential);
  ad5761_write(CMD_WR_UPDATE_DAC_REG, dacCode);
  delay(200); // Settle

  running = true;
  int skipCount = 10;
  Serial.println("START_CONFIRMED");

  float vramp = mapDACToVoltage(dacCode);
  uint32_t intervalMs = (uint32_t)(interval * 1000);
  uint32_t durationMs = (uint32_t)(duration * 1000);
  unsigned long startTime = millis();
  unsigned long lastSample = 0;

  while (running && (millis() - startTime < durationMs)) {
    unsigned long now = millis();
    if (now - lastSample >= intervalMs) {
      int16_t vout_d = ads.readADC_SingleEnded(0);
      if (vout_d >= 0) {
        if (skipCount > 0) { skipCount--; }
        else {
          Serial.print("DATA:");
          Serial.print(vramp, 4);
          Serial.print(",");
          Serial.println(vout_d);
        }
      }
      lastSample = now;
    }
    if (checkSerialCommands()) return;
  }

  running = false;
  resetDAC();
  Serial.println("CA complete.");
}

// LSV: LSV:<start_v>:<end_v>:<scan_rate>
void handleLSV(const String& cmd) {
  float f[3];
  int n = parseFields(cmd, cmd.indexOf(':') + 1, f, 3);
  if (n < 3) { Serial.println("Error: LSV needs 3 params"); return; }

  float startV = f[0], endV = f[1], scanRate = f[2];

  if (startV < -1.5 || startV > 1.5 || endV < -1.5 || endV > 1.5 ||
      startV == endV || scanRate <= 0) {
    Serial.println("Error: Parameters out of range!"); resetDAC(); return;
  }

  uint16_t startDAC = mapVoltageToDAC(startV);
  uint16_t endDAC   = mapVoltageToDAC(endV);
  uint16_t dacRange = (endDAC > startDAC) ? (endDAC - startDAC) : (startDAC - endDAC);
  uint16_t stepSize = max((uint16_t)1, (uint16_t)(dacRange / 1000));
  float voltRange = fabs(endV - startV);
  uint32_t sweepTimeMs = (uint32_t)((voltRange / scanRate) * 1000);
  uint32_t steps = dacRange / stepSize;
  uint32_t delayMs = steps > 0 ? sweepTimeMs / steps : 1;
  if (delayMs == 0) delayMs = 1;

  ad5761_write(CMD_WR_UPDATE_DAC_REG, startDAC);
  delay(200);

  running = true;
  int skipCount = 50;
  Serial.println("START_CONFIRMED");

  sweepSegment(startDAC, endDAC, stepSize, delayMs, &skipCount);

  running = false;
  resetDAC();
  Serial.println("LSV complete.");
}

// DPV: DPV:<start_v>:<end_v>:<step_v>:<pulse_v>:<pulse_period>:<pulse_width>
void handleDPV(const String& cmd) {
  float f[6];
  int n = parseFields(cmd, cmd.indexOf(':') + 1, f, 6);
  if (n < 6) { Serial.println("Error: DPV needs 6 params"); return; }

  float startV = f[0], endV = f[1], stepV = f[2];
  float pulseV = f[3], period = f[4], pulseWidth = f[5];

  if (startV < -1.5 || endV > 1.5 || stepV <= 0 || pulseV <= 0 ||
      period <= 0 || pulseWidth <= 0 || pulseWidth >= period) {
    Serial.println("Error: Parameters out of range!"); resetDAC(); return;
  }

  running = true;
  int skipCount = 10;
  Serial.println("START_CONFIRMED");

  uint32_t periodMs = (uint32_t)(period * 1000);
  uint32_t pulseMs  = (uint32_t)(pulseWidth * 1000);
  bool goingUp = (endV > startV);
  float baseV = startV;

  while (running) {
    if ((goingUp && baseV > endV) || (!goingUp && baseV < endV)) break;

    // Baseline: set voltage, wait for settling, then measure at end
    ad5761_write(CMD_WR_UPDATE_DAC_REG, mapVoltageToDAC(baseV));
    delay(periodMs - pulseMs);
    setAndMeasure(baseV, &skipCount);
    if (checkSerialCommands()) return;

    // Pulse: set voltage, wait for settling, then measure at end
    float pulseVoltage = baseV + pulseV;
    if (pulseVoltage > 1.5) pulseVoltage = 1.5;
    if (pulseVoltage < -1.5) pulseVoltage = -1.5;
    ad5761_write(CMD_WR_UPDATE_DAC_REG, mapVoltageToDAC(pulseVoltage));
    delay(pulseMs);
    setAndMeasure(pulseVoltage, &skipCount);
    if (checkSerialCommands()) return;

    // Step to next base potential
    baseV += goingUp ? stepV : -stepV;
  }

  running = false;
  resetDAC();
  Serial.println("DPV complete.");
}

// SWV: SWV:<start_v>:<end_v>:<step_v>:<pulse_v>:<frequency>
void handleSWV(const String& cmd) {
  float f[5];
  int n = parseFields(cmd, cmd.indexOf(':') + 1, f, 5);
  if (n < 5) { Serial.println("Error: SWV needs 5 params"); return; }

  float startV = f[0], endV = f[1], stepV = f[2];
  float pulseV = f[3], frequency = f[4];

  if (startV < -1.5 || endV > 1.5 || stepV <= 0 || pulseV <= 0 || frequency <= 0) {
    Serial.println("Error: Parameters out of range!"); resetDAC(); return;
  }

  running = true;
  int skipCount = 10;
  Serial.println("START_CONFIRMED");

  uint32_t halfPeriodMs = (uint32_t)(500.0 / frequency); // half period in ms
  if (halfPeriodMs == 0) halfPeriodMs = 1;
  bool goingUp = (endV > startV);
  float baseV = startV;

  while (running) {
    if ((goingUp && baseV > endV) || (!goingUp && baseV < endV)) break;

    // Forward pulse: set voltage, wait, then measure at end of half-period
    float fwdV = baseV + pulseV;
    if (fwdV > 1.5) fwdV = 1.5;
    ad5761_write(CMD_WR_UPDATE_DAC_REG, mapVoltageToDAC(fwdV));
    delay(halfPeriodMs);
    setAndMeasure(fwdV, &skipCount);
    if (checkSerialCommands()) return;

    // Reverse pulse: set voltage, wait, then measure at end of half-period
    float revV = baseV - pulseV;
    if (revV < -1.5) revV = -1.5;
    ad5761_write(CMD_WR_UPDATE_DAC_REG, mapVoltageToDAC(revV));
    delay(halfPeriodMs);
    setAndMeasure(revV, &skipCount);
    if (checkSerialCommands()) return;

    // Step to next base
    baseV += goingUp ? stepV : -stepV;
  }

  running = false;
  resetDAC();
  Serial.println("SWV complete.");
}

// NPV: NPV:<baseline_v>:<start_v>:<end_v>:<step_v>:<pulse_period>:<pulse_width>
void handleNPV(const String& cmd) {
  float f[6];
  int n = parseFields(cmd, cmd.indexOf(':') + 1, f, 6);
  if (n < 6) { Serial.println("Error: NPV needs 6 params"); return; }

  float baselineV = f[0], startV = f[1], endV = f[2];
  float stepV = f[3], period = f[4], pulseWidth = f[5];

  if (baselineV < -1.5 || baselineV > 1.5 || startV < -1.5 || endV > 1.5 ||
      stepV <= 0 || period <= 0 || pulseWidth <= 0 || pulseWidth >= period) {
    Serial.println("Error: Parameters out of range!"); resetDAC(); return;
  }

  running = true;
  int skipCount = 10;
  Serial.println("START_CONFIRMED");

  uint32_t periodMs = (uint32_t)(period * 1000);
  uint32_t pulseMs  = (uint32_t)(pulseWidth * 1000);
  bool goingUp = (endV > startV);
  float pulseV = startV;

  while (running) {
    if ((goingUp && pulseV > endV) || (!goingUp && pulseV < endV)) break;

    // Baseline: set voltage, wait, then measure at end
    ad5761_write(CMD_WR_UPDATE_DAC_REG, mapVoltageToDAC(baselineV));
    delay(periodMs - pulseMs);
    setAndMeasure(baselineV, &skipCount);
    if (checkSerialCommands()) return;

    // Pulse: set voltage, wait, then measure at end
    ad5761_write(CMD_WR_UPDATE_DAC_REG, mapVoltageToDAC(pulseV));
    delay(pulseMs);
    setAndMeasure(pulseV, &skipCount);
    if (checkSerialCommands()) return;

    // Step pulse potential
    pulseV += goingUp ? stepV : -stepV;
  }

  running = false;
  resetDAC();
  Serial.println("NPV complete.");
}

// POT: POT:<duration>:<sample_interval>
void handlePOT(const String& cmd) {
  float f[2];
  int n = parseFields(cmd, cmd.indexOf(':') + 1, f, 2);
  if (n < 2) { Serial.println("Error: POT needs 2 params"); return; }

  float duration = f[0], interval = f[1];

  if (duration <= 0 || interval <= 0) {
    Serial.println("Error: Parameters out of range!"); return;
  }

  // No DAC output for open-circuit potentiometry
  resetDAC();

  running = true;
  int skipCount = 5;
  Serial.println("START_CONFIRMED");

  uint32_t intervalMs = (uint32_t)(interval * 1000);
  uint32_t durationMs = (uint32_t)(duration * 1000);
  unsigned long startTime = millis();
  unsigned long lastSample = 0;

  while (running && (millis() - startTime < durationMs)) {
    unsigned long now = millis();
    if (now - lastSample >= intervalMs) {
      int16_t vout_d = ads.readADC_SingleEnded(0);
      if (vout_d >= 0) {
        if (skipCount > 0) { skipCount--; }
        else {
          Serial.print("DATA:0.0000,");
          Serial.println(vout_d);
        }
      }
      lastSample = now;
    }
    if (checkSerialCommands()) return;
  }

  running = false;
  Serial.println("POT complete.");
}

// ==================== Setup & Main Loop ====================

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }

  Serial.println("Starting SaxStat V03...");

  spi.begin(SCK_PIN, -1, MOSI_PIN, CS_PIN);
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);

  pinMode(GAIN1_PIN, OUTPUT);
  pinMode(GAIN2_PIN, OUTPUT);
  digitalWrite(GAIN1_PIN, LOW);
  digitalWrite(GAIN2_PIN, LOW);
  ad5761_write(CMD_SW_FULL_RESET, 0x0000);
  delay(10);
  ad5761_write(CMD_WR_CTRL_REG, CONTROL_REG_MINUS3_TO_PLUS3);
  delay(10);
  resetDAC();
  delay(5000);

  Wire.begin();
  Wire.setClock(100000);
  bool adsFound = false;
  for (uint8_t addr : {0x48, 0x49, 0x4A, 0x4B}) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      if (ads.begin(addr)) {
        adsFound = true;
        ads.setGain(GAIN_ONE);
        Serial.print("ADS1115 at 0x"); Serial.println(addr, HEX);
        break;
      }
    }
  }
  if (!adsFound) {
    Serial.println("Error: ADS1115 not found!");
    while (1) { delay(10); }
  }

  Serial.println("Ready.");
}

void loop() {
  static String inputBuffer = "";

  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      String command = inputBuffer;
      inputBuffer = "";
      command.trim();

      if (command.startsWith("START:"))     handleCV(command);
      else if (command.startsWith("CA:"))   handleCA(command);
      else if (command.startsWith("LSV:"))  handleLSV(command);
      else if (command.startsWith("DPV:"))  handleDPV(command);
      else if (command.startsWith("SWV:"))  handleSWV(command);
      else if (command.startsWith("NPV:"))  handleNPV(command);
      else if (command.startsWith("POT:"))  handlePOT(command);
      else if (command == "STOP") {
        running = false; resetDAC(); Serial.println("Stopped.");
      }
      else if (command == "CALIBRATE") {
        int16_t v = ads.readADC_SingleEnded(0);
        Serial.println(v >= 0 ? String(v) : "ADC:ERROR");
      }
      else if (command == "MODE_0") {
        currentMode = 0; digitalWrite(GAIN1_PIN, LOW); digitalWrite(GAIN2_PIN, LOW);
      }
      else if (command == "MODE_1") {
        currentMode = 1; digitalWrite(GAIN1_PIN, HIGH); digitalWrite(GAIN2_PIN, HIGH);
      }
    } else {
      inputBuffer += c;
    }
  }
}
