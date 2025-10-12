//The code for ESP32+AD5761 to generate a -1.5V to +1.5V, 0.2 Hz triangle wave.
#include "ad5761.h"
#include "register.h"
#include <SPI.h>

// Pin definitions for SPI communication
#define SCK_PIN   18  // SPI clock pin
#define MOSI_PIN  23  // SPI MOSI pin
#define CS_PIN     5  // Chip select pin

// Control register value for -3 V to +3 V range, straight binary, no overrange
#define CONTROL_REG_MINUS3_TO_PLUS3 0b000000000101101 // RA[2:0]=101, B2C=0, others default

// Initialize AD5761 DAC
void ad5761_init() {
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  SPI.begin(SCK_PIN, -1, MOSI_PIN, CS_PIN);
  Serial.println("Sending software full reset...");
  ad5761_write(CMD_SW_FULL_RESET, 0, 0);
  Serial.println("Writing control register (0x005D for -3 V to +3 V with Vref=2.5V)...");
  ad5761_write(CMD_WR_CTRL_REG, CONTROL_REG_MINUS3_TO_PLUS3, 0);
  // Read back control register to verify
  Serial.println("Reading back control register...");
  uint16_t ctrl_reg = ad5761_read(CMD_RD_CTRL_REG);
  Serial.print("Control register value: 0x");
  Serial.println(ctrl_reg, HEX);
  Serial.println("Setting DAC to -1.5 V (0x4000)...");
  ad5761_write(CMD_WR_UPDATE_DAC_REG, 16384, 0); // Start at -1.5 V
}

// Write data to AD5761 register via SPI
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
  delayMicroseconds(1); // Ensure CS toggle
}

// Read data from AD5761 register via SPI
uint16_t ad5761_read(uint8_t reg_addr_cmd) {
  uint8_t tx_data[3] = { reg_addr_cmd, 0, 0 };
  uint8_t rx_data[3] = { 0, 0, 0 };
  SPI.beginTransaction(SPISettings(AD5761_CLOCK_RATE, MSBFIRST, SPI_MODE2));
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(tx_data, 3); // Send read command
  digitalWrite(CS_PIN, HIGH);
  delayMicroseconds(1);
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(rx_data, 3); // Read response
  digitalWrite(CS_PIN, HIGH);
  SPI.endTransaction();
  return ((uint16_t)rx_data[1] << 8) | rx_data[2];
}

// Setup function
void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  Serial.println("Starting AD5761 initialization...");
  ad5761_init();
  Serial.println("AD5761 initialized; VOUT should be -1.5 V");
  Serial.println("Measure VOUT with multimeter for 5 seconds...");
  delay(5000); // Hold -1.5 V for testing
}

// Main loop: Generate 0.2 Hz triangle wave (-1.5 V to +1.5 V)
void loop() {
  const uint16_t min_val = 16384;    // 0x4000 = -1.5 V
  const uint16_t max_val = 49152;    // 0xC000 = +1.5 V
  const uint16_t step_size = 256;    // Increment by 256 for ~128 steps per half-cycle
  const uint16_t num_steps = (max_val - min_val) / step_size + 1; // ~128 steps
  const unsigned long period_us = 5000000; // 0.2 Hz = 5 s period
  const unsigned long half_period_us = period_us / 2; // 2.5 s per half-cycle
  const unsigned long step_delay_us = (half_period_us - (num_steps * 12UL)) / num_steps;
  static uint32_t cycle_count = 0;

  Serial.print("Starting triangle cycle (0.2 Hz), step_delay_us: ");
  Serial.println(step_delay_us);
  unsigned long cycle_start = micros();
  // Rising edge: -1.5 V to +1.5 V
  for (uint16_t i = min_val; i <= max_val; i += step_size) {
    ad5761_write(CMD_WR_UPDATE_DAC_REG, i, 0);
    delayMicroseconds(step_delay_us);
  }
  // Falling edge: +1.5 V to -1.5 V
  for (uint16_t i = max_val; i >= min_val; i -= step_size) {
    ad5761_write(CMD_WR_UPDATE_DAC_REG, i, 0);
    delayMicroseconds(step_delay_us);
  }
  unsigned long cycle_end = micros();
  Serial.print("Cycle complete, duration: ");
  Serial.print((cycle_end - cycle_start) / 1000.0);
  Serial.println(" ms");
  cycle_count++;
}
